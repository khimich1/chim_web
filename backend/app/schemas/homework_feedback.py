"""Pydantic schemas for teacher/student homework feedback (SPEC §1.9.9)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FeedbackContentBase(BaseModel):
    teacher_text: str | None = Field(default=None, max_length=4000)
    teacher_voice_id: uuid.UUID | None = None
    teacher_image_ids: list[uuid.UUID] = Field(default_factory=list, max_length=5)

    @field_validator("teacher_image_ids")
    @classmethod
    def validate_image_count(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(value) > 5:
            raise ValueError("At most 5 feedback images allowed")
        return value


class StepFeedbackUpsert(FeedbackContentBase):
    """PUT body for per-step teacher feedback."""


class SubmissionFeedbackUpsert(FeedbackContentBase):
    """PUT body for submission-level teacher feedback."""


class FeedbackContentRead(BaseModel):
    teacher_text: str | None = None
    teacher_voice_url: str | None = None
    teacher_image_urls: list[str] = Field(default_factory=list)
    published_at: datetime | None = None


class StepFeedbackRead(FeedbackContentRead):
    position: int
    title: str | None = None


class StudentHomeworkFeedbackRead(BaseModel):
    has_feedback: bool
    steps: list[StepFeedbackRead] = Field(default_factory=list)
    submission: FeedbackContentRead | None = None

    model_config = ConfigDict(from_attributes=True)
