"""Notification endpoints (teacher-only).

| Method | Path                              | Role    | Description      |
|--------|-----------------------------------|---------|------------------|
| GET    | /api/notifications                | teacher | List             |
| GET    | /api/notifications/unread-count     | teacher | Unread badge     |
| PATCH  | /api/notifications/{id}/read      | teacher | Mark as read     |
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TeacherUser
from app.db.session import get_db
from app.schemas.notifications import NotificationRead, UnreadCount
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[NotificationRead]:
    return await NotificationService(db).list_notifications(teacher)


@router.get("/unread-count", response_model=UnreadCount)
async def unread_count(
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UnreadCount:
    return await NotificationService(db).unread_count(teacher)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: uuid.UUID,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationRead:
    return await NotificationService(db).mark_read(teacher, notification_id)
