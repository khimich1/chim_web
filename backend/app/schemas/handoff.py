"""Schemas for QR handoff / mobile capture (SPEC §1.9.9)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HandoffCreateResponse(BaseModel):
    token: uuid.UUID
    capture_url: str
    expires_at: datetime


class FeedbackHandoffCreate(BaseModel):
    position: int | None = None


class CaptureMetaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    purpose: Literal["answer", "feedback"] = "answer"
    session_id: uuid.UUID | None = None
    homework_id: uuid.UUID | None = None
    position: int | None = None
    task_title: str | None = None
    question_preview: str | None = None
    expires_at: datetime
    already_has_photo: bool
    staged_image_id: uuid.UUID | None = None
    staged_image_url: str | None = None


class CaptureUploadResponse(BaseModel):
    purpose: Literal["answer", "feedback"] = "answer"
    position: int | None = None
    answer_image_ids: list[uuid.UUID] = Field(default_factory=list)
    answer_image_urls: list[str] = Field(default_factory=list)
    staged_image_id: uuid.UUID | None = None
    staged_image_url: str | None = None
