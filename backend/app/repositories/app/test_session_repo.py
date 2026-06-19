"""Data access for TestSession / TestSessionStep (app DB)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import TestSession, TestSessionStatus
from app.models.enums import ExamTrack, StepStatus


@dataclass(frozen=True, slots=True)
class IncorrectStepRow:
    test_id: int
    session_id: uuid.UUID
    track: ExamTrack
    checked_at: datetime | None


class TestSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, test_session: TestSession) -> TestSession:
        self._session.add(test_session)
        await self._session.flush()
        return test_session

    async def get_with_steps(
        self, session_id: uuid.UUID
    ) -> TestSession | None:
        stmt = (
            select(TestSession)
            .where(TestSession.id == session_id)
            .options(selectinload(TestSession.steps))
        )
        return await self._session.scalar(stmt)

    async def find_latest_active(
        self,
        student_id: uuid.UUID,
        *,
        variant_ref: str | None = None,
        homework_assignment_id: uuid.UUID | None = None,
        practice_task_type: int | None = None,
    ) -> TestSession | None:
        stmt = select(TestSession).where(
            TestSession.student_id == student_id,
            TestSession.status == TestSessionStatus.IN_PROGRESS,
        )
        if variant_ref is not None:
            stmt = stmt.where(
                TestSession.variant_ref == variant_ref,
                TestSession.homework_assignment_id.is_(None),
                TestSession.practice_task_type.is_(None),
            )
        if homework_assignment_id is not None:
            stmt = stmt.where(
                TestSession.homework_assignment_id == homework_assignment_id,
            )
        if practice_task_type is not None:
            stmt = stmt.where(
                TestSession.practice_task_type == practice_task_type,
                TestSession.variant_ref.is_(None),
                TestSession.homework_assignment_id.is_(None),
            )
        stmt = stmt.order_by(
            TestSession.created_at.desc(),
            TestSession.id.desc(),
        ).limit(1)
        return await self._session.scalar(stmt)

    async def list_incorrect_steps(
        self,
        student_id: uuid.UUID,
        *,
        limit: int = 20,
        exclude_session_id: uuid.UUID | None = None,
    ) -> list[IncorrectStepRow]:
        """Return recent incorrect checked steps for a student (newest first)."""
        from app.models import TestSessionStep

        stmt = (
            select(
                TestSessionStep.test_id,
                TestSessionStep.session_id,
                TestSession.track,
                TestSessionStep.checked_at,
            )
            .join(TestSession, TestSessionStep.session_id == TestSession.id)
            .where(
                TestSession.student_id == student_id,
                TestSessionStep.status == StepStatus.CHECKED,
                TestSessionStep.is_correct.is_(False),
            )
            .order_by(
                TestSessionStep.checked_at.desc().nullslast(),
                TestSessionStep.id.desc(),
            )
            .limit(max(1, limit))
        )
        if exclude_session_id is not None:
            stmt = stmt.where(TestSession.id != exclude_session_id)

        result = await self._session.execute(stmt)
        return [
            IncorrectStepRow(
                test_id=row.test_id,
                session_id=row.session_id,
                track=row.track,
                checked_at=row.checked_at,
            )
            for row in result.all()
        ]
