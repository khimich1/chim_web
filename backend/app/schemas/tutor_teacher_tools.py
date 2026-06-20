"""Pydantic schemas for teacher-facing tutor tools (Task 45)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.models.enums import ExamTrack
from app.schemas.homework import HomeworkItem
from app.schemas.tutor_student_tools import MistakeByType


class StudentActivitySummary(BaseModel):
    tutor_sessions: int = 0
    completed_test_sessions: int = 0
    submitted_homework: int = 0


class StudentSummary(BaseModel):
    student_id: uuid.UUID
    email: str
    track: ExamTrack
    weak_topics: list[str] = Field(default_factory=list)
    mistakes_by_type: list[MistakeByType] = Field(default_factory=list)
    total_incorrect_steps: int = 0
    activity: StudentActivitySummary


class HomeworkDraftPreview(BaseModel):
    """Draft homework for teacher review — not persisted by the tool."""

    student_id: uuid.UUID
    title: str
    description: str | None = None
    items: list[HomeworkItem]
    is_draft: bool = True
    note: str = (
        "Черновик. Создайте ДЗ через UI или POST /api/homework после подтверждения."
    )


class ClassMistakeAggregate(BaseModel):
    task_type: int
    topic: str | None = None
    mistake_count: int
    affected_students: int


class ClassOverview(BaseModel):
    total_students: int
    total_incorrect_steps: int
    by_type: list[ClassMistakeAggregate]
