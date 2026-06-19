"""Schemas for Stepik-style test sessions.

Step views never expose `correct_ans`, hints, or detailed explanations.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ExamTrack, StepStatus, TestSessionStatus


class SessionCreate(BaseModel):
    # Required for free practice; ignored for homework sessions, where the server
    # aggregates test items from the assignment (possibly several variants).
    variant_ref: str | None = Field(default=None, max_length=64)
    # Optional subset of `type` numbers for partial homework; None = full variant.
    types: list[int] | None = None
    homework_assignment_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _require_scope(self) -> SessionCreate:
        has_homework = self.homework_assignment_id is not None
        has_variant = bool((self.variant_ref or "").strip())
        has_types_only = (
            not has_homework
            and not has_variant
            and self.types is not None
            and len(self.types) > 0
        )
        if has_homework or has_variant or has_types_only:
            return self
        raise ValueError(
            "Provide variant_ref, types (without variant), or homework_assignment_id"
        )


class StepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position: int
    test_id: int
    type: int
    question: str
    options: str | None = None
    status: StepStatus
    answer: str | None = None
    is_correct: bool | None = None
    hint_used: bool


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    track: ExamTrack
    variant_ref: str | None = None
    homework_assignment_id: uuid.UUID | None = None
    status: TestSessionStatus
    score: int | None = None
    max_score: int | None = None
    total_steps: int
    created_at: datetime
    steps: list[StepRead]


class StepCheckRequest(BaseModel):
    answer: str = Field(max_length=512)


class StepCheckResponse(BaseModel):
    position: int
    is_correct: bool
    status: StepStatus


class SessionSummaryStep(BaseModel):
    position: int
    test_id: int
    type: int
    is_correct: bool | None = None
    hint_used: bool


class ActiveSessionResponse(BaseModel):
    session_id: uuid.UUID | None = None


class SessionSummary(BaseModel):
    id: uuid.UUID
    status: TestSessionStatus
    score: int
    max_score: int
    completed_at: datetime | None = None
    steps: list[SessionSummaryStep]
