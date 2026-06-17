"""Pydantic schemas for tutor chat API."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TutorPageContext(BaseModel):
    topic: str | None = None
    test_session_id: uuid.UUID | None = None
    homework_id: uuid.UUID | None = None


class TutorSessionCreate(BaseModel):
    page_context: TutorPageContext | None = None


class TutorSourceCitation(BaseModel):
    source: Literal["lecture", "lecture_qa"] | None = None
    topic: str | None = None
    chunk_idx: int | None = None
    chunk_title: str | None = None


class TutorMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    sources: list[TutorSourceCitation] | None = None
    created_at: datetime


class TutorSessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role_context: Literal["student", "teacher"]
    page_context: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class TutorSessionDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role_context: Literal["student", "teacher"]
    page_context: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[TutorMessageRead]


class TutorMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


class TutorMessageResponse(BaseModel):
    message_id: uuid.UUID
    role: Literal["assistant"] = "assistant"
    content: str
    sources: list[TutorSourceCitation] = Field(default_factory=list)


class TutorHealthResponse(BaseModel):
    rag_index_exists: bool
    openai_configured: bool
