"""Pydantic schemas for homework assignments and submissions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import HomeworkItemKind, HomeworkStatus


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

    @field_validator("types")
    @classmethod
    def validate_types(cls, value: list[int]) -> list[int]:
        if any(item < 1 for item in value):
            raise ValueError("types must be positive integers")
        return value


HomeworkItem = Annotated[
    LectureItem | TestVariantItem | TestPartialItem | TestByTypeItem,
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


class HomeworkSubmitRequest(BaseModel):
    test_session_id: uuid.UUID | None = None
