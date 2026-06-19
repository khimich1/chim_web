"""Pydantic schemas for student activity ledger and stats (Phase 13, §1.8)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class StudentStatsRead(BaseModel):
    """Aggregated gamification metrics for a student (API Task 61)."""

    student_id: uuid.UUID
    total_points: int = 0
    week_points: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    last_active_date: date | None = None
    tasks_solved: int = 0
    total_minutes: int = 0
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class RecordEventResult(BaseModel):
    """Outcome of an idempotent activity event write."""

    created: bool
    points_awarded: int = 0


class LeaderboardEntry(BaseModel):
    """Public leaderboard row (no email)."""

    rank: int = Field(ge=1)
    display_name: str
    points: int = Field(ge=0)


class TeacherStudentStatsRead(BaseModel):
    """Teacher-facing student row with gamification metrics (Task 62)."""

    id: uuid.UUID
    email: str
    display_name: str | None = None
    total_points: int = 0
    week_points: int = 0
    streak: int = 0
    tasks_solved: int = 0
    total_minutes: int = 0
    last_active_date: date | None = None
