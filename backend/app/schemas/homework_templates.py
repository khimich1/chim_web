"""Pydantic schemas for homework templates."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.homework import HomeworkItem


class HomeworkTemplateCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    items: list[HomeworkItem] = Field(min_length=1, max_length=10)


class HomeworkTemplateUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    items: list[HomeworkItem] | None = Field(default=None, min_length=1, max_length=10)


class HomeworkTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    teacher_id: uuid.UUID
    title: str
    description: str | None = None
    items: list[dict]
    created_at: datetime
    updated_at: datetime


class HomeworkTemplateAssignRequest(BaseModel):
    """Assign a template to one student or one group (exactly one target)."""

    student_id: uuid.UUID | None = None
    group_id: uuid.UUID | None = None
    due_at: datetime | None = None

    @model_validator(mode="after")
    def exactly_one_target(self) -> HomeworkTemplateAssignRequest:
        has_student = self.student_id is not None
        has_group = self.group_id is not None
        if has_student == has_group:
            raise ValueError("Provide exactly one of student_id or group_id")
        return self
