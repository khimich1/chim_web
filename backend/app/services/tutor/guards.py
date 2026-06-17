"""Guardrails for the chemistry tutor agent (ported from RAG_chemistry)."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, MessagesState

PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b\d{4}\s\d{6}\b"), "[ПАСПОРТ]"),
    (
        re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            re.IGNORECASE,
        ),
        "[EMAIL]",
    ),
    (re.compile(r"\b(?:\d[ -]*?){15,16}\d\b"), "[КАРТА]"),
]

INJECTION_PATTERNS = re.compile(
    r"(?:\[SYSTEM\]|"
    r"ignore\s+(?:all\s+)?(?:previous|prior)|disregard|"
    r"new\s+instructions?|override|you\s+are\s+now|forget\s+(?:all\s+)?"
    r"(?:previous|prior)?|"
    r"игнорируй(?:те)?\s+(?:все\s+)?(?:предыдущие|ранее)?|"
    r"забудь(?:те)?\s+(?:все\s+)?(?:предыдущие|инструкции)?|"
    r"нов(?:ые|ая)\s+инструкц|"
    r"теперь\s+ты\s+|"
    r"системн(?:ое|ая)\s+сообщен|"
    r"раскрой\s+секрет|"
    r"jailbreak)",
    re.IGNORECASE | re.DOTALL,
)

_OFF_TOPIC_REPLY = (
    "Я помощник по подготовке к ЕГЭ/ОГЭ по химии. Помогаю с теорией, разбором "
    "заданий и вопросами по школьной химии. Задайте вопрос по этим темам."
)

_THEORY_TOOLS = frozenset({"retrieve_theory"})


def mask_pii(text: str) -> str:
    out = text
    for pattern, placeholder in PII_PATTERNS:
        out = pattern.sub(placeholder, out)
    return out


def contains_injection(text: str) -> bool:
    return bool(INJECTION_PATTERNS.search(text))


def sanitize_theory_payload(raw: str) -> str:
    try:
        hits = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw
    if not isinstance(hits, list):
        return raw

    clean: list[dict[str, Any]] = []
    for item in hits:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content", "") or "")
        if contains_injection(content):
            continue
        clean.append(item)
    return json.dumps(clean, ensure_ascii=False)


def make_is_on_topic_checker(llm) -> Callable[[str], bool]:
    def is_on_topic(user_message: str) -> bool:
        system = (
            "Ты классификатор релевантности. Определи, относится ли сообщение "
            "пользователя к подготовке по химии: теория, элементы, реакции, "
            "органическая/неорганическая химия, задачи ЕГЭ/ОГЭ по химии, "
            "разбор заданий, учебные вопросы школьника.\n"
            "Ответь ровно одним словом: да — если тема подходит, нет — если запрос "
            "про другое (рецепты, код, политику, спорт, произвольный чат и т.п.)."
        )
        resp = llm.invoke(
            [SystemMessage(content=system), HumanMessage(content=user_message)]
        )
        answer = (resp.content or "").strip().lower()
        return answer.startswith("да") or answer.startswith("yes")

    return is_on_topic


def make_input_guard(is_on_topic: Callable[[str], bool]):
    def input_guard(state: MessagesState) -> dict:
        messages = state["messages"]
        if not messages:
            return {}
        last_msg = messages[-1]
        if not isinstance(last_msg, HumanMessage):
            return {}

        content = last_msg.content
        if not isinstance(content, str):
            content = str(content)

        # B3: classify every incoming user turn, not just the first. With history
        # replayed from PostgreSQL (stateless graph) `len(messages) > 1` on every
        # turn, so a first-message-only check would let off-topic requests slip
        # through after one on-topic question.
        if not is_on_topic(content):
            return {"messages": [AIMessage(content=_OFF_TOPIC_REPLY)]}
        return {}

    return input_guard


def route_after_input_guard(state: MessagesState) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage):
        return END
    return "agent"


def tool_output_guard(state: MessagesState) -> dict:
    messages = state["messages"]
    if not messages:
        return {}
    last_msg = messages[-1]
    if not isinstance(last_msg, ToolMessage):
        return {}
    if last_msg.name not in _THEORY_TOOLS:
        return {}

    raw = last_msg.content
    if not isinstance(raw, str):
        return {}

    cleaned = sanitize_theory_payload(raw)
    if cleaned == raw:
        return {}

    cleaned_msg = ToolMessage(
        content=cleaned,
        tool_call_id=last_msg.tool_call_id,
        name=last_msg.name,
        id=getattr(last_msg, "id", None),
    )
    return {"messages": [cleaned_msg]}
