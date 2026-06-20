"""Data access for tutor sessions and messages."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import flag_modified

from app.models import (
    TutorMessage,
    TutorMessageRole,
    TutorSession,
    TutorUserProfile,
    UserRole,
)


class TutorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(
        self,
        *,
        user_id: uuid.UUID,
        role_context: UserRole,
        page_context: dict[str, Any] | None = None,
    ) -> TutorSession:
        tutor_session = TutorSession(
            user_id=user_id,
            role_context=role_context,
            page_context=page_context,
        )
        self._session.add(tutor_session)
        await self._session.flush()
        await self._session.refresh(tutor_session)
        return tutor_session

    async def list_sessions_for_user(self, user_id: uuid.UUID) -> list[TutorSession]:
        stmt = (
            select(TutorSession)
            .where(TutorSession.user_id == user_id)
            .options(joinedload(TutorSession.messages))
            .order_by(TutorSession.updated_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result.unique().all())

    async def list_sessions_for_student(
        self,
        student_user_id: uuid.UUID,
    ) -> list[TutorSession]:
        return await self.list_sessions_for_user(student_user_id)

    async def get_session(self, session_id: uuid.UUID) -> TutorSession | None:
        # B2: transcript order is guaranteed by the relationship-level
        # `order_by="TutorMessage.created_at"` on TutorSession.messages, which
        # joinedload applies to the eager-loaded collection.
        stmt = (
            select(TutorSession)
            .where(TutorSession.id == session_id)
            .options(joinedload(TutorSession.messages))
        )
        return await self._session.scalar(stmt)

    async def list_messages(self, session_id: uuid.UUID) -> list[TutorMessage]:
        """Ordered message history for a session (used to replay into the agent)."""
        stmt = (
            select(TutorMessage)
            .where(TutorMessage.session_id == session_id)
            .order_by(TutorMessage.created_at)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def delete_message(self, message_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(TutorMessage).where(TutorMessage.id == message_id)
        )
        await self._session.flush()

    async def add_message(
        self,
        *,
        session_id: uuid.UUID,
        role: TutorMessageRole,
        content: str,
        sources: list[dict[str, Any]] | None = None,
    ) -> TutorMessage:
        message = TutorMessage(
            session_id=session_id,
            role=role,
            content=content,
            sources=sources,
        )
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def get_profile_data(self, user_id: uuid.UUID) -> dict[str, Any]:
        row = await self._session.get(TutorUserProfile, user_id)
        if row is None or not isinstance(row.data, dict):
            return {}
        return dict(row.data)

    async def upsert_profile_key(
        self,
        user_id: uuid.UUID,
        key: str,
        value: str,
    ) -> dict[str, Any]:
        row = await self._session.get(TutorUserProfile, user_id)
        if row is None:
            row = TutorUserProfile(user_id=user_id, data={})
            self._session.add(row)
        data = dict(row.data) if isinstance(row.data, dict) else {}
        data[str(key)] = value
        row.data = data
        flag_modified(row, "data")
        await self._session.flush()
        return data
