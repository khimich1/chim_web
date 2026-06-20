"""Schemas for Stepik-style test sessions.

Step views never expose `correct_ans`, hints, or detailed explanations.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    ExamTrack,
    GradingMode,
    StepStatus,
    TestSessionSource,
    TestSessionStatus,
)


class SessionCreate(BaseModel):
    # Required for free practice; ignored for homework sessions, where the server
    # aggregates test items from the assignment (possibly several variants).
    variant_ref: str | None = Field(default=None, max_length=64)
    # Optional subset of `type` numbers for partial homework; None = full variant.
    types: list[int] | None = None
    homework_assignment_id: uuid.UUID | None = None
    # Custom theme session (SPEC §1.9.5).
    custom_theme_id: uuid.UUID | None = None
    task_ids: list[uuid.UUID] | None = None

    @model_validator(mode="after")
    def _require_scope(self) -> SessionCreate:
        has_homework = self.homework_assignment_id is not None
        has_variant = bool((self.variant_ref or "").strip())
        has_custom = self.custom_theme_id is not None
        has_types_only = (
            not has_homework
            and not has_variant
            and not has_custom
            and self.types is not None
            and len(self.types) > 0
        )
        if has_homework or has_variant or has_types_only or has_custom:
            if has_custom and (has_homework or has_variant or has_types_only):
                raise ValueError(
                    "custom_theme_id cannot be combined with exam session fields"
                )
            if has_custom and self.task_ids is not None and len(self.task_ids) == 0:
                raise ValueError("task_ids must be non-empty when provided")
            return self
        raise ValueError(
            "Provide variant_ref, types (without variant), homework_assignment_id, "
            "or custom_theme_id"
        )


class StepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position: int
    test_id: int | None = None
    custom_task_id: uuid.UUID | None = None
    type: int | None = None
    question: str | None = None
    options: str | None = None
    question_blocks: list[dict] | None = None
    grading_mode: GradingMode | None = None
    status: StepStatus
    answer: str | None = None
    answer_image_id: uuid.UUID | None = None
    answer_image_url: str | None = None
    is_correct: bool | None = None
    hint_used: bool


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    track: ExamTrack
    source: TestSessionSource = TestSessionSource.EXAM
    variant_ref: str | None = None
    homework_assignment_id: uuid.UUID | None = None
    custom_theme_id: uuid.UUID | None = None
    status: TestSessionStatus
    score: int | None = None
    max_score: int | None = None
    total_steps: int
    created_at: datetime
    steps: list[StepRead]


class StepCheckRequest(BaseModel):
    answer: str = Field(max_length=512)


class StepAttachAnswerImageRequest(BaseModel):
    answer_image_id: uuid.UUID


class StepAttachAnswerImageResponse(BaseModel):
    position: int
    answer_image_id: uuid.UUID
    answer_image_url: str


class StepCheckResponse(BaseModel):
    position: int
    is_correct: bool
    status: StepStatus


class StepCompareResponse(BaseModel):
    position: int
    status: StepStatus
    reference_answer: list[dict]


class SessionSummaryStep(BaseModel):
    position: int
    test_id: int | None = None
    custom_task_id: uuid.UUID | None = None
    type: int | None = None
    grading_mode: GradingMode | None = None
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
