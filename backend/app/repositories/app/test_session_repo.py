"""Data access for TestSession / TestSessionStep (app DB)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import TestSession


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
