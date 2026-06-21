"""Pydantic schemas for homework assignments and submissions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import HomeworkItemKind, HomeworkStatus, GradingMode, StepStatus


class LectureItem(BaseModel):
    kind: Literal[HomeworkItemKind.LECTURE] = HomeworkItemKind.LECTURE
    topic: str = Field(min_length=1, max_length=200)
    chunk_idxs: list[int] | None = None


class TestVariantItem(BaseModel):
    kind: Literal[HomeworkItemKind.TEST_VARIANT] = HomeworkItemKind.TEST_VARIANT
    variant: str = Field(min_length=1, max_length=64)


class TestPartialItem(BaseModel):
    kind: Literal[HomeworkItemKind.TEST_PARTIAL] = HomeworkItemKind.TEST_PARTIAL
    variant: str = Field(min_length=1, max_length=64)
    types: list[int] = Field(min_length=1)

    @field_validator("types")
    @classmethod
    def validate_types(cls, value: list[int]) -> list[int]:
        if any(item < 1 for item in value):
            raise ValueError("types must be positive integers")
        return value


class TestByTypeItem(BaseModel):
    """Task number(s) drawn from every variant (EGE) or full type file (OGE)."""

    kind: Literal[HomeworkItemKind.TEST_BY_TYPE] = HomeworkItemKind.TEST_BY_TYPE
    types: list[int] = Field(min_length=1)
    variants: list[str] | None = None

    @field_validator("types")
    @classmethod
    def validate_types(cls, value: list[int]) -> list[int]:
        if any(item < 1 for item in value):
            raise ValueError("types must be positive integers")
        return value

    @field_validator("variants")
    @classmethod
    def validate_variants(cls, value: list[str] | None) -> list[str] | None:
        if value is not None and len(value) == 0:
            raise ValueError("variants must be non-empty when provided")
        return value


class CustomThemeHomeworkItem(BaseModel):
    kind: Literal[HomeworkItemKind.CUSTOM_THEME] = HomeworkItemKind.CUSTOM_THEME
    theme_id: uuid.UUID
    task_ids: list[uuid.UUID] | None = None

    @field_validator("task_ids")
    @classmethod
    def validate_task_ids(cls, value: list[uuid.UUID] | None) -> list[uuid.UUID] | None:
        if value is not None and len(value) == 0:
            raise ValueError("task_ids must be non-empty when provided")
        return value


HomeworkItem = Annotated[
    LectureItem
    | TestVariantItem
    | TestPartialItem
    | TestByTypeItem
    | CustomThemeHomeworkItem,
    Field(discriminator="kind"),
]


class HomeworkCreate(BaseModel):
    student_id: uuid.UUID
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    due_at: datetime | None = None
    items: list[HomeworkItem] = Field(min_length=1, max_length=10)


class HomeworkSubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    submitted_at: datetime
    test_session_id: uuid.UUID | None = None
    score: int | None = None
    max_score: int | None = None
    answered_steps: int | None = None
    total_steps: int | None = None
    completion_percent: int | None = None


class StepFeedbackEmbeddedRead(BaseModel):
    """Existing teacher feedback embedded in homework review (§1.9.9)."""

    teacher_text: str | None = None
    teacher_voice_url: str | None = None
    teacher_image_urls: list[str] = Field(default_factory=list)
    published_at: datetime | None = None


class HomeworkSubmissionStepRead(BaseModel):
    """Self-check step photo for teacher review (SPEC §1.9.8–1.9.9, AC-7.9, AC-7.11)."""

    position: int
    custom_task_id: uuid.UUID | None = None
    title: str | None = None
    grading_mode: GradingMode | None = None
    question_blocks: list[dict] = Field(default_factory=list)
    reference_answer: list[dict] | None = None
    answer: str | None = None
    answer_image_url: str | None = None
    status: StepStatus
    feedback: StepFeedbackEmbeddedRead | None = None


class HomeworkItemProgressRead(BaseModel):
    """Per-item completion state for a multi-item assignment (SPEC §1.7)."""

    model_config = ConfigDict(from_attributes=True)

    item_index: int
    kind: HomeworkItemKind
    completed: bool


class HomeworkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    student_email: str | None = None
    title: str
    description: str | None = None
    due_at: datetime | None = None
    items: list[dict]
    status: HomeworkStatus
    created_at: datetime
    submission: HomeworkSubmissionRead | None = None
    progress: list[HomeworkItemProgressRead] = Field(default_factory=list)
    active_test_session_id: uuid.UUID | None = None
    submission_steps: list[HomeworkSubmissionStepRead] = Field(default_factory=list)
    submission_feedback: StepFeedbackEmbeddedRead | None = None
    has_teacher_feedback: bool = False
    can_reopen: bool = False


class HomeworkSubmitRequest(BaseModel):
    test_session_id: uuid.UUID | None = None
