"""Data access for student activity events and stats (app DB)."""

from __future__ import annotations

import uuid
from typing import Any

from typing import Literal

from sqlalchemy import desc, exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ActivityEventType,
    StudentActivityEvent,
    StudentProfile,
    StudentStats,
    User,
)

LeaderboardPeriod = Literal["week", "all_time"]

_LEARNING_ACTIVITY_TYPES = (
    ActivityEventType.STEP_CORRECT,
    ActivityEventType.HOMEWORK_COMPLETE,
    ActivityEventType.ONBOARDING_FIRST_ACTION,
)


class ActivityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_event(
        self,
        student_id: uuid.UUID,
        event_type: ActivityEventType,
        ref_id: str,
    ) -> StudentActivityEvent | None:
        stmt = select(StudentActivityEvent).where(
            StudentActivityEvent.student_id == student_id,
            StudentActivityEvent.event_type == event_type,
            StudentActivityEvent.ref_id == ref_id,
        )
        return await self._session.scalar(stmt)

    async def has_learning_activity(self, student_id: uuid.UUID) -> bool:
        stmt = select(
            exists().where(
                StudentActivityEvent.student_id == student_id,
                StudentActivityEvent.event_type.in_(_LEARNING_ACTIVITY_TYPES),
            )
        )
        return bool(await self._session.scalar(stmt))

    async def list_student_ids_with_learning_activity(
        self,
        student_ids: list[uuid.UUID],
    ) -> set[uuid.UUID]:
        if not student_ids:
            return set()
        stmt = (
            select(StudentActivityEvent.student_id)
            .where(
                StudentActivityEvent.student_id.in_(student_ids),
                StudentActivityEvent.event_type.in_(_LEARNING_ACTIVITY_TYPES),
            )
            .distinct()
        )
        result = await self._session.scalars(stmt)
        return set(result.all())

    async def try_create_event(
        self,
        *,
        student_id: uuid.UUID,
        event_type: ActivityEventType,
        ref_id: str,
        points: int,
        payload: dict[str, Any] | None = None,
    ) -> StudentActivityEvent | None:
        """Insert event; return None when unique constraint blocks duplicate."""
        event = StudentActivityEvent(
            student_id=student_id,
            event_type=event_type,
            ref_id=ref_id,
            points=points,
            payload=payload or {},
        )
        async with self._session.begin_nested():
            self._session.add(event)
            try:
                await self._session.flush()
            except IntegrityError:
                return None
        return event

    async def get_stats(self, student_id: uuid.UUID) -> StudentStats | None:
        return await self._session.get(StudentStats, student_id)

    async def get_or_create_stats(self, student_id: uuid.UUID) -> StudentStats:
        stats = await self.get_stats(student_id)
        if stats is not None:
            return stats
        stats = StudentStats(student_id=student_id)
        self._session.add(stats)
        await self._session.flush()
        return stats

    async def list_leaderboard(
        self,
        *,
        period: LeaderboardPeriod,
        limit: int,
    ) -> list[tuple[StudentStats, str | None]]:
        """Top students by week or all-time points with optional public display name."""
        points_column = (
            StudentStats.week_points
            if period == "week"
            else StudentStats.total_points
        )
        stmt = (
            select(StudentStats, StudentProfile.display_name)
            .outerjoin(
                StudentProfile,
                StudentProfile.user_id == StudentStats.student_id,
            )
            .order_by(desc(points_column), StudentStats.student_id)
            .limit(limit)
        )
        rows = await self._session.execute(stmt)
        return list(rows.all())

    async def list_teacher_students_stats(
        self,
        teacher_id: uuid.UUID,
    ) -> list[tuple[User, StudentProfile, StudentStats | None]]:
        """Students owned by teacher with optional stats (zeros when missing)."""
        stmt = (
            select(User, StudentProfile, StudentStats)
            .join(StudentProfile, StudentProfile.user_id == User.id)
            .outerjoin(StudentStats, StudentStats.student_id == User.id)
            .where(StudentProfile.teacher_id == teacher_id)
            .order_by(User.created_at.desc())
        )
        rows = await self._session.execute(stmt)
        return list(rows.all())
