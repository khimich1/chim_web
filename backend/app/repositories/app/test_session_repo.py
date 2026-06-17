"""Data access for TestSession / TestSessionStep (app DB)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import TestSession, TestSessionStatus


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
    ) -> TestSession | None:
        stmt = select(TestSession).where(
            TestSession.student_id == student_id,
            TestSession.status == TestSessionStatus.IN_PROGRESS,
        )
        if variant_ref is not None:
            stmt = stmt.where(
                TestSession.variant_ref == variant_ref,
                TestSession.homework_assignment_id.is_(None),
            )
        if homework_assignment_id is not None:
            stmt = stmt.where(
                TestSession.homework_assignment_id == homework_assignment_id,
            )
        stmt = stmt.order_by(
            TestSession.created_at.desc(),
            TestSession.id.desc(),
        ).limit(1)
        return await self._session.scalar(stmt)
