"""Lead capture schemas for marketing funnel."""

from __future__ import annotations

import re
import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LeadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=10, max_length=20)
    school_class: Literal["8", "9", "10", "11"]
    goal: Literal["ege", "oge", "school"]
    comment: str | None = Field(default=None, max_length=1000)
    source_page: str = Field(max_length=200)
    utm_source: str | None = Field(default=None, max_length=100)
    utm_medium: str | None = Field(default=None, max_length=100)
    utm_campaign: str | None = Field(default=None, max_length=100)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) == 11 and digits.startswith("8"):
            digits = "7" + digits[1:]
        if len(digits) != 11 or not digits.startswith("7"):
            raise ValueError("Invalid RU phone")
        return f"+{digits}"


class LeadCreated(BaseModel):
    id: uuid.UUID
    status: Literal["accepted"] = "accepted"
