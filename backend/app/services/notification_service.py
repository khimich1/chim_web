"""In-app notification business logic."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole
from app.repositories.app.notification_repo import NotificationRepository
from app.schemas.notifications import NotificationRead, UnreadCount


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = NotificationRepository(session)
        self._session = session

    async def list_notifications(self, teacher: User) -> list[NotificationRead]:
        if teacher.role != UserRole.TEACHER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher role required",
            )
        notifications = await self._repo.list_for_user(teacher.id)
        return [NotificationRead.model_validate(item) for item in notifications]

    async def unread_count(self, teacher: User) -> UnreadCount:
        if teacher.role != UserRole.TEACHER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher role required",
            )
        count = await self._repo.count_unread(teacher.id)
        return UnreadCount(count=count)

    async def mark_read(
        self,
        teacher: User,
        notification_id: uuid.UUID,
    ) -> NotificationRead:
        notification = await self._repo.get_by_id(notification_id)
        if notification is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )
        if notification.user_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your notification",
            )
        await self._repo.mark_read(notification)
        await self._session.commit()
        return NotificationRead.model_validate(notification)
