"""Server-side gating for solve-pipeline during active test sessions (SPEC §1.3.4)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import TestSession, TestSessionStatus
from app.models.enums import StepStatus


@dataclass(frozen=True, slots=True)
class IncorrectStepGate:
    """Validated explain_incorrect_step scope for one checked wrong step."""

    test_session_id: uuid.UUID
    step_position: int
    test_id: int
    student_answer: str | None


async def resolve_incorrect_step_gate(
    db: AsyncSession,
    *,
    student_id: uuid.UUID,
    page_context: dict[str, Any] | None,
) -> IncorrectStepGate | None:
    """Return gate only when page_context matches a checked incorrect step in DB."""
    if not page_context:
        return None
    if page_context.get("solve_mode") != "explain_incorrect_step":
        return None

    raw_session_id = page_context.get("test_session_id")
    raw_position = page_context.get("step_position")
    raw_test_id = page_context.get("test_id")
    if raw_session_id is None or raw_position is None or raw_test_id is None:
        return None

    try:
        session_id = uuid.UUID(str(raw_session_id))
        step_position = int(raw_position)
        test_id = int(raw_test_id)
    except (TypeError, ValueError):
        return None

    if step_position < 0 or test_id <= 0:
        return None

    stmt = (
        select(TestSession)
        .where(
            TestSession.id == session_id,
            TestSession.student_id == student_id,
            TestSession.status == TestSessionStatus.IN_PROGRESS,
        )
        .options(selectinload(TestSession.steps))
    )
    session = await db.scalar(stmt)
    if session is None:
        return None

    step = next((s for s in session.steps if s.position == step_position), None)
    if step is None:
        return None
    if step.status != StepStatus.CHECKED or step.is_correct is not False:
        return None
    if step.test_id != test_id:
        return None

    return IncorrectStepGate(
        test_session_id=session_id,
        step_position=step_position,
        test_id=test_id,
        student_answer=step.answer,
    )
