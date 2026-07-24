"""Student request/response schemas (teacher-managed learners)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.security import MIN_PASSWORD_LENGTH
from app.models.enums import ExamTrack
from app.schemas.login_id import LOGIN_MAX_LENGTH, LOGIN_MIN_LENGTH, normalize_login


class StudentCreate(BaseModel):
    email: str = Field(
        min_length=LOGIN_MIN_LENGTH,
        max_length=LOGIN_MAX_LENGTH,
        description="Login (stored in users.email)",
    )
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)
    track: ExamTrack

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_as_login(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("Login must be a string")
        return normalize_login(v)


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    track: ExamTrack
    created_at: datetime
    first_login_at: datetime | None = None
    onboarding_completed_at: datetime | None = None
    is_activated: bool = False


class StudentPasswordResetRead(BaseModel):
    """Returned once after password reset — show to teacher immediately."""

    temporary_password: str
