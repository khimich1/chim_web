"""Deterministic critic for solve-pipeline drafts (Stage A — code only)."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from app.services.tutor.solve.state import Critique, SolveState
from app.services.tutor.validation import validate_draft

MAX_CRITIC_RETRIES = 2


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


def make_critic_node():
    def critic(state: SolveState) -> dict[str, Any]:
        critique = run_code_critic(state)
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
