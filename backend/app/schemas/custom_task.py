"""Pydantic schemas for teacher themes and custom tasks (SPEC §1.9)."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import GradingMode

_IMAGE_URL_RE = re.compile(
    r"^/api/uploads/images/[0-9a-f]{8}-"
    r"[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


class ContentBlock(BaseModel):
    type: Literal["text", "image"]
    content: str | None = None
    url: str | None = None

    @model_validator(mode="after")
    def validate_block(self) -> ContentBlock:
        if self.type == "text":
            if not self.content or not self.content.strip():
                raise ValueError("text block requires non-empty content")
            if self.url is not None:
                raise ValueError("text block must not include url")
        else:
            if not self.url:
                raise ValueError("image block requires url")
            if self.content is not None:
                raise ValueError("image block must not include content")
            if not _IMAGE_URL_RE.match(self.url):
                raise ValueError(
                    "image url must match /api/uploads/images/{id} format"
                )
        return self


class ThemeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    is_published: bool = False
    sort_order: int = 0


class ThemeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    is_published: bool | None = None
    sort_order: int | None = None


class ThemeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    teacher_id: uuid.UUID
    title: str
    description: str | None = None
    is_published: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class CustomTaskCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    sort_order: int = 0
    grading_mode: GradingMode
    question_blocks: list[ContentBlock] = Field(min_length=1)
    reference_answer: list[ContentBlock] | None = None
    correct_value: str | None = Field(default=None, max_length=512)

    @model_validator(mode="after")
    def validate_grading_fields(self) -> CustomTaskCreate:
        if self.grading_mode == GradingMode.AUTO:
            if not self.correct_value or not self.correct_value.strip():
                raise ValueError("auto grading_mode requires correct_value")
        elif self.grading_mode == GradingMode.SELF_CHECK:
            if not self.reference_answer:
                raise ValueError(
                    "self_check grading_mode requires reference_answer blocks"
                )
        return self


class CustomTaskUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    sort_order: int | None = None
    grading_mode: GradingMode | None = None
    question_blocks: list[ContentBlock] | None = Field(
        default=None,
        min_length=1,
    )
    reference_answer: list[ContentBlock] | None = None
    correct_value: str | None = Field(default=None, max_length=512)

    @model_validator(mode="after")
    def validate_grading_fields(self) -> CustomTaskUpdate:
        if self.grading_mode == GradingMode.AUTO:
            if self.correct_value is not None and not self.correct_value.strip():
                raise ValueError("auto grading_mode requires correct_value")
        return self


class CustomTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    theme_id: uuid.UUID
    title: str | None = None
    sort_order: int
    grading_mode: GradingMode
    question_blocks: list[dict]
    reference_answer: list[dict] | None = None
    correct_value: str | None = None
    created_at: datetime
    updated_at: datetime
