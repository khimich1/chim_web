"""Pydantic schemas for in-app notifications."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import NotificationType


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: NotificationType
    payload: dict[str, Any]
    read_at: datetime | None = None
    created_at: datetime


class UnreadCount(BaseModel):
    count: int
