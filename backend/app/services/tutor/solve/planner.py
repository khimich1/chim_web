"""LLM planner for complex solve-pipeline task types (§17.2, stage B)."""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.services.tutor.context import TutorRunContext, get_tutor_context
from app.services.tutor.llm_utils import invoke_llm
from app.services.tutor.solve.state import SolvePlan, SolveState
from app.services.tutor.validation import detect_answer_format

logger = logging.getLogger(__name__)

COMPLEX_TASK_TYPES = frozenset({7, 8, 26, 27, 28})


def needs_planner(task_type: int | None) -> bool:
    return task_type in COMPLEX_TASK_TYPES


class _PlannerLLMOutput(BaseModel):
    intent: Literal["solve_task", "theory", "search_tasks", "profile", "other"] = "solve_task"
    rag_queries: list[str] = Field(default_factory=list)
    sub_steps: list[str] = Field(default_factory=list)


def _build_planner_messages(state: SolveState) -> list[SystemMessage | HumanMessage]:
    task_context = state.get("task_context") or {}
    theory_hits = state.get("theory_hits") or []
    answer_format = state.get("answer_format") or "digit_string"
    task_type = task_context.get("type")

    theory_summary = "\n".join(
        f"- {hit.get('topic')} — {hit.get('chunk_title')}"
        for hit in theory_hits[:4]
        if hit.get("topic") or hit.get("chunk_title")
    ) or "нет фрагментов"

    system = SystemMessage(
        content=(
            "Ты — планировщик разбора задания по химии (ЕГЭ/ОГЭ).\n"
            "Верни JSON: intent, rag_queries (1–3 запроса к учебнику), "
            "sub_steps (пошаговый план разбора).\n"
            "intent = solve_task. sub_steps не должны противоречить условию."
        )
    )
    user = HumanMessage(
        content=(
            f"## Задание (type={task_type}, format={answer_format})\n"
            f"{task_context.get('question', '')}\n\n"
            f"## Уже найденные фрагменты учебника\n{theory_summary}\n\n"
            "Составь план: rag_queries и sub_steps для solver."
        )
    )
    return [system, user]


def _default_plan(state: SolveState) -> SolvePlan:
    task_context = state.get("task_context") or {}
    task_id = state.get("task_id") or task_context.get("id")
    task_type = task_context.get("type")
    correct_ans = state.get("correct_ans") or ""
    answer_format = state.get("answer_format") or detect_answer_format(
        int(task_type) if task_type is not None else 0,
        correct_ans,
    )
    return SolvePlan(
        intent="solve_task",
        task_id=int(task_id) if task_id is not None else None,
        rag_queries=[],
        sub_steps=[],
        answer_format=answer_format,
    )


def _plan_from_parsed(parsed: _PlannerLLMOutput, state: SolveState) -> SolvePlan:
    base = _default_plan(state)
    return base.model_copy(
        update={
            "intent": parsed.intent,
            "rag_queries": parsed.rag_queries[:3],
            "sub_steps": parsed.sub_steps,
        }
    )


def _plan_from_text(content: str, state: SolveState) -> SolvePlan:
    try:
        parsed = _PlannerLLMOutput.model_validate_json(content)
    except Exception:
        try:
            parsed = _PlannerLLMOutput.model_validate(json.loads(content))
        except Exception:
            logger.warning("planner: failed to parse LLM output, using default plan")
            return _default_plan(state)
    return _plan_from_parsed(parsed, state)


def _invoke_planner_llm(
    llm: ChatOpenAI,
    messages: list[SystemMessage | HumanMessage],
    ctx: TutorRunContext,
) -> _PlannerLLMOutput | None:
    try:
        structured = llm.with_structured_output(_PlannerLLMOutput)
        result = structured.invoke(messages)
        if isinstance(result, _PlannerLLMOutput):
            return result
    except (AttributeError, NotImplementedError, TypeError):
        pass

    response = invoke_llm(llm, messages, ctx)
    raw = response.content if isinstance(response.content, str) else str(response.content)
    try:
        return _PlannerLLMOutput.model_validate_json(raw)
    except Exception:
        return None


def make_planner_node(llm: ChatOpenAI, ctx: TutorRunContext | None = None):
    def planner(state: SolveState) -> dict[str, Any]:
        run_ctx = ctx or get_tutor_context()
        messages = _build_planner_messages(state)
        parsed = _invoke_planner_llm(llm, messages, run_ctx)
        plan = _plan_from_parsed(parsed, state) if parsed else _default_plan(state)

        payload: dict[str, Any] = {"plan": plan.model_dump()}
        if plan.answer_format:
            payload["answer_format"] = plan.answer_format
        return payload

    return planner
