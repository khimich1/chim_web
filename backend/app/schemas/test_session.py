"""Schemas for Stepik-style test sessions.

Step views never expose `correct_ans`. Hint and detailed explanation are
returned only by their dedicated endpoints / after an explicit check.
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
    def _require_variant_for_free_practice(self) -> SessionCreate:
        if self.homework_assignment_id is None and not (self.variant_ref or "").strip():
            raise ValueError("variant_ref is required when no homework_assignment_id")
        return self


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
    # Populated on resume for checked steps (SPEC §1.3.2).
    detailed_explanation: str | None = None


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
    steps: list[StepRead]


class StepCheckRequest(BaseModel):
    answer: str = Field(max_length=512)


class StepCheckResponse(BaseModel):
    position: int
    is_correct: bool
    status: StepStatus
    detailed_explanation: str | None = None


class HintResponse(BaseModel):
    hint: str | None = None


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
