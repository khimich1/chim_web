"""Auth request/response schemas.

Note: `email` is the wire field name for the login identifier (stored in
users.email). It is a plain `str` (not Pydantic EmailStr). Format checks for
*creating* a login live on StudentCreate; login only normalizes case.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ExamTrack, UserRole
from app.schemas.login_id import LOGIN_MAX_LENGTH, LOGIN_MIN_LENGTH


class LoginRequest(BaseModel):
    email: str = Field(
        min_length=LOGIN_MIN_LENGTH,
        max_length=LOGIN_MAX_LENGTH,
        description="Login (stored in users.email)",
    )
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_login_id(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("Login must be a string")
        return v.strip().lower()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: UserRole
    track: ExamTrack | None = None
