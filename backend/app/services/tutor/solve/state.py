"""Solve-pipeline graph state and DTOs (tutor-rag §17.3)."""

from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import MessagesState
from pydantic import BaseModel, Field
from typing_extensions import NotRequired

AnswerFormat = Literal["digit_string", "number"]


class SolvePlan(BaseModel):
    intent: Literal["solve_task", "theory", "search_tasks", "profile", "other"] = "solve_task"
    task_id: int | None = None
    rag_queries: list[str] = Field(default_factory=list)
    sub_steps: list[str] = Field(default_factory=list)
    answer_format: AnswerFormat = "digit_string"


class Critique(BaseModel):
    approved: bool
    issues: list[str] = Field(default_factory=list)
    fix_instructions: str = ""


class SolveState(MessagesState):
    """Extended tutor graph state for the solve branch."""

    plan: NotRequired[dict[str, Any] | None]
    task_id: NotRequired[int | None]
    task_context: NotRequired[dict[str, Any] | None]
    correct_ans: NotRequired[str | None]
    theory_hits: NotRequired[list[dict[str, Any]]]
    draft_answer: NotRequired[str | None]
    student_answer: NotRequired[str | None]
    critique: NotRequired[dict[str, Any] | None]
    retry_count: NotRequired[int]
    answer_format: NotRequired[Literal["digit_string", "number"] | None]
    fix_instructions: NotRequired[str | None]
