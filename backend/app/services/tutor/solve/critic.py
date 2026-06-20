"""Deterministic + LLM critic for solve-pipeline drafts (§17.2 stage A/B)."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.services.tutor.context import TutorRunContext, get_tutor_context
from app.services.tutor.llm_utils import invoke_llm
from app.services.tutor.solve.planner import needs_planner
from app.services.tutor.solve.state import Critique, SolveState
from app.services.tutor.validation import validate_draft

logger = logging.getLogger(__name__)

MAX_CRITIC_RETRIES = 2


class _ChemicalCritiqueOutput(BaseModel):
    approved: bool
    issues: list[str] = Field(default_factory=list)
    fix_instructions: str = ""


def run_code_critic(state: SolveState) -> Critique:
    draft = (state.get("draft_answer") or "").strip()
    task_context = state.get("task_context") or {}
    issues = validate_draft(
        draft,
        correct_ans=state.get("correct_ans") or "",
        answer_format=state.get("answer_format") or "digit_string",
        theory_hits=state.get("theory_hits") or [],
        question=str(task_context.get("question") or ""),
        task_type=task_context.get("type"),
    )
    if not issues:
        return Critique(approved=True)
    fix = "Исправь ответ:\n" + "\n".join(f"- {issue}" for issue in issues)
    return Critique(approved=False, issues=issues, fix_instructions=fix)


def _build_chemical_critic_messages(state: SolveState) -> list[SystemMessage | HumanMessage]:
    task_context = state.get("task_context") or {}
    draft = (state.get("draft_answer") or "").strip()
    system = SystemMessage(
        content=(
            "Ты — химический рецензент разбора задания ЕГЭ/ОГЭ.\n"
            "Проверь химическую согласованность: формулы, соответствия, расчёты, "
            "логика шагов и отсутствие противоречий с условием и учебником.\n"
            "Верни JSON: approved (bool), issues (список), fix_instructions (кратко)."
        )
    )
    user = HumanMessage(
        content=(
            f"## Условие (type={task_context.get('type')})\n"
            f"{task_context.get('question', '')}\n\n"
            f"## Черновик разбора\n{draft}\n\n"
            "Одобри только если химия и логика шагов согласованы."
        )
    )
    return [system, user]


def _invoke_chemical_critic_llm(
    llm: ChatOpenAI,
    messages: list[SystemMessage | HumanMessage],
    ctx: TutorRunContext,
) -> _ChemicalCritiqueOutput | None:
    try:
        structured = llm.with_structured_output(_ChemicalCritiqueOutput)
        result = structured.invoke(messages)
        if isinstance(result, _ChemicalCritiqueOutput):
            return result
    except (AttributeError, NotImplementedError, TypeError):
        pass

    response = invoke_llm(llm, messages, ctx)
    raw = response.content if isinstance(response.content, str) else str(response.content)
    try:
        return _ChemicalCritiqueOutput.model_validate_json(raw)
    except Exception:
        try:
            return _ChemicalCritiqueOutput.model_validate(json.loads(raw))
        except Exception:
            logger.warning("chemical critic: failed to parse LLM output, approving")
            return None


def run_llm_chemical_critic(
    state: SolveState,
    llm: ChatOpenAI,
    ctx: TutorRunContext | None = None,
) -> Critique:
    run_ctx = ctx or get_tutor_context()
    messages = _build_chemical_critic_messages(state)
    parsed = _invoke_chemical_critic_llm(llm, messages, run_ctx)
    if parsed is None:
        return Critique(approved=True)
    if parsed.approved:
        return Critique(approved=True)
    issues = parsed.issues or ["химическая несогласованность разбора"]
    fix = parsed.fix_instructions.strip() or (
        "Исправь химические ошибки:\n" + "\n".join(f"- {issue}" for issue in issues)
    )
    return Critique(approved=False, issues=issues, fix_instructions=fix)


def run_critic(state: SolveState, llm: ChatOpenAI | None = None, ctx: TutorRunContext | None = None) -> Critique:
    code_critique = run_code_critic(state)
    if not code_critique.approved:
        return code_critique

    task_type = (state.get("task_context") or {}).get("type")
    if llm is not None and needs_planner(task_type):
        return run_llm_chemical_critic(state, llm, ctx)
    return code_critique


def make_critic_node(llm: ChatOpenAI | None = None, ctx: TutorRunContext | None = None):
    def critic(state: SolveState) -> dict[str, Any]:
        critique = run_critic(state, llm=llm, ctx=ctx)
        payload = critique.model_dump()
        if critique.approved:
            return {
                "critique": payload,
                "messages": [AIMessage(content=state.get("draft_answer") or "")],
            }
        return {
            "critique": payload,
            "fix_instructions": critique.fix_instructions,
            "retry_count": int(state.get("retry_count") or 0) + 1,
        }

    return critic


def route_after_critic(state: SolveState) -> str:
    critique_data = state.get("critique") or {}
    if critique_data.get("approved"):
        return "end"
    retries = int(state.get("retry_count") or 0)
    if retries <= MAX_CRITIC_RETRIES:
        return "solver"
    return "answer_finalize"


def make_answer_finalize_node():
    def answer_finalize(state: SolveState) -> dict[str, Any]:
        draft = (state.get("draft_answer") or "").strip()
        correct_ans = state.get("correct_ans") or "?"
        critique = state.get("critique") or {}
        issues = critique.get("issues") or []
        issue_text = "; ".join(issues) if issues else "не прошёл автоматическую проверку"
        content = (
            f"{draft}\n\n"
            "---\n"
            f"⚠️ Автопроверка: {issue_text}.\n"
            f"**Эталонный ответ:** {correct_ans}\n"
            "Сверьте разбор с учебником или спросите преподавателя."
        )
        return {"messages": [AIMessage(content=content)]}

    return answer_finalize
