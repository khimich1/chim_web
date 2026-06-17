"""Intent routing for tutor graph (theory vs solve-pipeline)."""

from __future__ import annotations

from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState

from app.services.tutor.context import TutorRunContext, get_tutor_context
from app.services.tutor.solve.task_flow import extract_task_id

IntentRoute = Literal["general_agent", "solve_pipeline"]


def should_use_solve_pipeline(
    user_message: str,
    ctx: TutorRunContext | None = None,
) -> bool:
    """True when message asks to solve a task and gating allows it."""
    ctx = ctx or get_tutor_context()
    if extract_task_id(user_message) is None:
        return False
    if ctx.role == "student" and ctx.active_test_session_id is not None:
        return False
    return True


def route_intent(
    state: MessagesState,
    ctx: TutorRunContext | None = None,
) -> IntentRoute:
    """Decide whether to enter solve-pipeline or the general ReAct agent."""
    ctx = ctx or get_tutor_context()
    last = state["messages"][-1]
    if not isinstance(last, HumanMessage):
        return "general_agent"
    content = last.content if isinstance(last.content, str) else str(last.content)
    if should_use_solve_pipeline(content, ctx):
        return "solve_pipeline"
    return "general_agent"
