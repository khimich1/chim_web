"""Pydantic schemas for teacher student groups."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StudentGroupCreate(BaseModel):
    name: str | None = Field(default=None, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str):
            return value.strip()
        return value


class StudentGroupUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be blank")
        return cleaned


class StudentGroupMembersReplace(BaseModel):
    student_ids: list[uuid.UUID] = Field(default_factory=list)


class StudentGroupMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    track: str | None = None


class StudentGroupSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    teacher_id: uuid.UUID
    name: str
    member_count: int = 0
    created_at: datetime


class StudentGroupDetailRead(StudentGroupSummaryRead):
    members: list[StudentGroupMemberRead] = Field(default_factory=list)
