"""Schemas for QR handoff / mobile capture (SPEC §1.9.9)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HandoffCreateResponse(BaseModel):
    token: uuid.UUID
    capture_url: str
    expires_at: datetime


class CaptureMetaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: uuid.UUID
    position: int
    task_title: str | None = None
    question_preview: str | None = None
    expires_at: datetime
    already_has_photo: bool


class CaptureUploadResponse(BaseModel):
    position: int
    answer_image_id: uuid.UUID
    answer_image_url: str
