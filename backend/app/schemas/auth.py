"""Auth request/response schemas.

Note: `email` is a plain `str` (not Pydantic EmailStr) to avoid the extra
`email-validator` dependency; format checks are not security-critical for login.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ExamTrack, UserRole


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: UserRole
    track: ExamTrack | None = None
