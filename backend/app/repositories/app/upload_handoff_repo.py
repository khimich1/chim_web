"""Data access for UploadHandoffToken rows (app DB)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UploadHandoffToken


class UploadHandoffTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_token(self, token: uuid.UUID) -> UploadHandoffToken | None:
        return await self._session.get(UploadHandoffToken, token)

    async def create(
        self,
        *,
        session_id: uuid.UUID,
        position: int,
        student_id: uuid.UUID,
        expires_at: datetime,
    ) -> UploadHandoffToken:
        record = UploadHandoffToken(
            session_id=session_id,
            position=position,
            student_id=student_id,
            expires_at=expires_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def invalidate_unused_for_step(
        self,
        session_id: uuid.UUID,
        position: int,
        *,
        invalidated_at: datetime,
    ) -> None:
        stmt = (
            update(UploadHandoffToken)
            .where(
                UploadHandoffToken.session_id == session_id,
                UploadHandoffToken.position == position,
                UploadHandoffToken.used_at.is_(None),
            )
            .values(expires_at=invalidated_at)
        )
        await self._session.execute(stmt)

    async def mark_used(
        self,
        record: UploadHandoffToken,
        used_at: datetime,
    ) -> None:
        record.used_at = used_at
        await self._session.flush()
