"""Adapt student questions into textbook search queries (Task 41.4 / A8)."""

from __future__ import annotations

import logging
import re
from typing import Protocol

from app.core.config import Settings, get_settings
from app.services.rag.keyword import tokenize

logger = logging.getLogger(__name__)

_MAX_QUERIES = 3

# Substance stem → extra search lines for multi-query retrieval (rule-based fallback).
_SUBSTANCE_RULES: tuple[tuple[re.Pattern[str], str, tuple[str, ...]], ...] = (
    (
        re.compile(r"\bсер[аыуео]?\b", re.IGNORECASE),
        "сера",
        (
            "сера металлы сульфиды",
            "реакции серы с металлами S Cu CuS CaS",
            "получение свойства сероводорода сера металлы",
        ),
    ),
    (
        re.compile(r"\bкарбонов\w*\s+кислот", re.IGNORECASE),
        "карбоновые кислоты",
        (
            "химические свойства карбоновых кислот",
            "получение карбоновых кислот реакции",
        ),
    ),
    (
        re.compile(r"\bалкан\w*\b", re.IGNORECASE),
        "алканы",
        ("химические свойства алканов CnH2n+2",),
    ),
)


class QueryRewriter(Protocol):
    def rewrite(
        self,
        question: str,
        *,
        page_context_topic: str | None = None,
    ) -> list[str]: ...


def rewrite_queries(
    question: str,
    *,
    page_context_topic: str | None = None,
    settings: Settings | None = None,
) -> list[str]:
    """Return 1–3 search queries for multi-query retrieval."""
    text = question.strip()
    if not text:
        return []

    app_settings = settings or get_settings()
    llm_queries = _rewrite_with_llm(text, page_context_topic=page_context_topic, settings=app_settings)
    if llm_queries:
        return _normalize_queries(llm_queries, original=text)

    return _normalize_queries(
        _rewrite_rule_based(text, page_context_topic=page_context_topic),
        original=text,
    )


def _rewrite_rule_based(
    question: str,
    *,
    page_context_topic: str | None = None,
) -> list[str]:
    queries: list[str] = [question]
    q_lower = question.lower()

    for pattern, _label, extras in _SUBSTANCE_RULES:
        if pattern.search(q_lower):
            queries.extend(extras)

    if page_context_topic:
        topic_lower = page_context_topic.strip().lower()
        if topic_lower and topic_lower in q_lower:
            queries.append(f"{page_context_topic.strip()} {question}")

    return queries


def _rewrite_with_llm(
    question: str,
    *,
    page_context_topic: str | None = None,
    settings: Settings,
) -> list[str] | None:
    if not settings.openai_api_key:
        return None
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
    except ImportError:
        logger.debug("langchain-openai not installed; using rule-based query rewrite")
        return None

    topic_hint = ""
    if page_context_topic:
        topic_hint = (
            f"\nТекущая тема страницы (мягкий сигнал, не жёсткий фильтр): "
            f"{page_context_topic}"
        )

    system = (
        "Ты помощник по химии. Преобразуй вопрос ученика в 1–3 коротких поисковых "
        "запроса для учебника по химии (ЕГЭ/ОГЭ). Используй термины учебника: "
        "названия веществ, формулы, типы реакций. Ответь только строками запросов, "
        "по одному на строку, без нумерации."
        f"{topic_hint}"
    )

    try:
        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
            max_tokens=120,
        )
        response = llm.invoke(
            [
                SystemMessage(content=system),
                HumanMessage(content=question),
            ]
        )
        content = getattr(response, "content", "")
        if not isinstance(content, str) or not content.strip():
            return None
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            return None
        logger.info(
            "rag.query_rewrite llm question_len=%d variants=%d",
            len(question),
            len(lines),
        )
        return lines
    except Exception:
        logger.exception("LLM query rewrite failed; falling back to rule-based")
        return None


def _normalize_queries(candidates: list[str], *, original: str) -> list[str]:
    """Deduplicate, drop empty/token-less queries, cap at _MAX_QUERIES."""
    seen: set[str] = set()
    result: list[str] = []

    for candidate in [original, *candidates]:
        text = candidate.strip()
        if not text or not tokenize(text):
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
        if len(result) >= _MAX_QUERIES:
            break

    return result or ([original] if original.strip() else [])
