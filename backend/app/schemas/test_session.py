"""Schemas for Stepik-style test sessions.

Step views never expose `correct_ans`. Hint and detailed explanation are
returned only by their dedicated endpoints / after an explicit check.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ExamTrack, StepStatus, TestSessionStatus


class SessionCreate(BaseModel):
    variant_ref: str = Field(min_length=1, max_length=64)
    # Optional subset of `type` numbers for partial homework; None = full variant.
    types: list[int] | None = None


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
    variant_ref: str
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


class SessionSummary(BaseModel):
    id: uuid.UUID
    status: TestSessionStatus
    score: int
    max_score: int
    completed_at: datetime | None = None
    steps: list[SessionSummaryStep]
