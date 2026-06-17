"""Data access for in-app notifications (app DB)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, notification: Notification) -> Notification:
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def list_for_user(self, user_id: uuid.UUID) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def count_unread(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
        return int(await self._session.scalar(stmt) or 0)

    async def get_by_id(self, notification_id: uuid.UUID) -> Notification | None:
        return await self._session.scalar(
            select(Notification).where(Notification.id == notification_id)
        )

    async def mark_read(self, notification: Notification) -> Notification:
        if notification.read_at is None:
            notification.read_at = datetime.now(timezone.utc)
            await self._session.flush()
        return notification
