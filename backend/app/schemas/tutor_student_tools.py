"""Pydantic schemas for student-facing tutor tools (Task 43)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import HomeworkStatus


class HomeworkToolItem(BaseModel):
    id: uuid.UUID
    title: str
    status: HomeworkStatus
    due_at: datetime | None = None
    items_count: int
    completed_items: int
    active_test_session_id: uuid.UUID | None = None


class MistakeByType(BaseModel):
    task_type: int
    topic: str | None = None
    mistake_count: int
    recent_test_ids: list[int] = Field(default_factory=list)


class MistakeAnalysis(BaseModel):
    total_incorrect_steps: int
    by_type: list[MistakeByType]


class TopicRecommendation(BaseModel):
    topic: str
    priority: int
    mistake_count: int
    related_task_types: list[int] = Field(default_factory=list)
    reason: str


class PracticeTask(BaseModel):
    """Practice item without correct_ans (Task 44)."""

    id: int
    type: int
    question: str


class SelfCheckItem(BaseModel):
    """Self-check Q/A from lecture_qa chunks (Task 44)."""

    question: str
    answer: str
    chunk_idx: int
    chunk_title: str | None = None
