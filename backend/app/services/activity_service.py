"""Student activity ledger and gamification stats (Phase 13, SPEC §1.8)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityEventType, StudentStats
from app.repositories.app.activity_repo import ActivityRepository, LeaderboardPeriod
from app.schemas.activity import (
    LeaderboardEntry,
    RecordEventResult,
    StudentStatsRead,
    TeacherStudentStatsRead,
)

POINTS_STEP_CORRECT = 10
POINTS_HOMEWORK_COMPLETE = 50
POINTS_STREAK_DAILY = 5
POINTS_STREAK_WEEKLY = 30


def _utc_now(now: datetime | None = None) -> datetime:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _utc_today(now: datetime | None = None) -> date:
    return _utc_now(now).date()


def _iso_week_key(value: date) -> str:
    year, week, _ = value.isocalendar()
    return f"{year}-W{week:02d}"


def resolve_public_display_name(
    display_name: str | None,
    student_id: uuid.UUID,
) -> str:
    """Public leaderboard label; never expose email."""
    if display_name and display_name.strip():
        return display_name.strip()
    return f"Ученик-{student_id.hex[:8]}"


class ActivityService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ActivityRepository(session)

    async def record_event(
        self,
        student_id: uuid.UUID,
        event_type: ActivityEventType,
        ref_id: str,
        points: int,
        *,
        payload: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> RecordEventResult:
        """Append ledger event once; duplicate (student, type, ref) awards no points."""
        event = await self._repo.try_create_event(
            student_id=student_id,
            event_type=event_type,
            ref_id=ref_id,
            points=points,
            payload=payload,
        )
        if event is None:
            return RecordEventResult(created=False, points_awarded=0)

        stats = await self._repo.get_or_create_stats(student_id)
        event_date = _utc_now(occurred_at).date()
        self._apply_points_to_stats(stats, points, event_date)
        return RecordEventResult(created=True, points_awarded=points)

    async def record_step_correct(
        self,
        student_id: uuid.UUID,
        step_id: uuid.UUID,
        *,
        payload: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> RecordEventResult:
        """Award +10 for a first-time correct step; update streak bonuses."""
        result = await self.record_event(
            student_id,
            ActivityEventType.STEP_CORRECT,
            str(step_id),
            POINTS_STEP_CORRECT,
            payload=payload,
            occurred_at=occurred_at,
        )
        if not result.created:
            return result

        stats = await self._repo.get_or_create_stats(student_id)
        stats.tasks_solved += 1
        active_date = _utc_today(occurred_at)
        await self._update_streak_for_new_active_day(stats, student_id, active_date)
        return result

    async def record_homework_complete(
        self,
        student_id: uuid.UUID,
        assignment_id: uuid.UUID,
        *,
        points: int | None = None,
        payload: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> RecordEventResult:
        """Award homework points on first submit (idempotent per assignment)."""
        awarded = points if points is not None else POINTS_HOMEWORK_COMPLETE
        return await self.record_event(
            student_id,
            ActivityEventType.HOMEWORK_COMPLETE,
            str(assignment_id),
            awarded,
            payload=payload,
            occurred_at=occurred_at,
        )

    async def record_homework_complete_delta(
        self,
        student_id: uuid.UUID,
        assignment_id: uuid.UUID,
        delta_points: int,
        *,
        answered_steps: int,
        payload: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> RecordEventResult:
        """Award extra homework points after resubmit (idempotent per answered count)."""
        if delta_points <= 0:
            return RecordEventResult(created=False, points_awarded=0)
        return await self.record_event(
            student_id,
            ActivityEventType.HOMEWORK_COMPLETE_DELTA,
            f"{assignment_id}:{answered_steps}",
            delta_points,
            payload=payload,
            occurred_at=occurred_at,
        )

    async def record_onboarding_welcome_viewed(
        self,
        student_id: uuid.UUID,
    ) -> RecordEventResult:
        return await self.record_event(
            student_id,
            ActivityEventType.ONBOARDING_WELCOME_VIEWED,
            "welcome",
            0,
        )

    async def record_onboarding_welcome_completed(
        self,
        student_id: uuid.UUID,
    ) -> RecordEventResult:
        return await self.record_event(
            student_id,
            ActivityEventType.ONBOARDING_WELCOME_COMPLETED,
            "welcome",
            0,
        )

    async def record_onboarding_welcome_skipped(
        self,
        student_id: uuid.UUID,
    ) -> RecordEventResult:
        return await self.record_event(
            student_id,
            ActivityEventType.ONBOARDING_WELCOME_SKIPPED,
            "welcome",
            0,
        )

    async def record_onboarding_checklist_step(
        self,
        student_id: uuid.UUID,
        step: str,
    ) -> RecordEventResult:
        return await self.record_event(
            student_id,
            ActivityEventType.ONBOARDING_CHECKLIST_STEP,
            step,
            0,
            payload={"step": step},
        )

    async def record_onboarding_first_action(
        self,
        student_id: uuid.UUID,
        action_type: str,
    ) -> RecordEventResult:
        return await self.record_event(
            student_id,
            ActivityEventType.ONBOARDING_FIRST_ACTION,
            action_type,
            0,
            payload={"action_type": action_type},
        )

    async def has_learning_activity(self, student_id: uuid.UUID) -> bool:
        return await self._repo.has_learning_activity(student_id)

    async def add_session_minutes(
        self,
        student_id: uuid.UUID,
        minutes: int,
    ) -> StudentStatsRead:
        """Accumulate completed test-session duration in total_minutes."""
        if minutes < 0:
            raise ValueError("minutes must be non-negative")
        stats = await self._repo.get_or_create_stats(student_id)
        stats.total_minutes += minutes
        await self._session.flush()
        await self._session.refresh(stats)
        return StudentStatsRead.model_validate(stats)

    async def get_stats(self, student_id: uuid.UUID) -> StudentStatsRead:
        stats = await self._repo.get_or_create_stats(student_id)
        await self._session.refresh(stats)
        return StudentStatsRead.model_validate(stats)

    async def get_teacher_students_stats(
        self,
        teacher_id: uuid.UUID,
    ) -> list[TeacherStudentStatsRead]:
        rows = await self._repo.list_teacher_students_stats(teacher_id)
        entries: list[TeacherStudentStatsRead] = []
        for user, profile, stats in rows:
            entries.append(
                TeacherStudentStatsRead(
                    id=user.id,
                    email=user.email,
                    display_name=profile.display_name,
                    total_points=stats.total_points if stats else 0,
                    week_points=stats.week_points if stats else 0,
                    streak=stats.current_streak if stats else 0,
                    tasks_solved=stats.tasks_solved if stats else 0,
                    total_minutes=stats.total_minutes if stats else 0,
                    last_active_date=stats.last_active_date if stats else None,
                )
            )
        return entries

    async def get_leaderboard(
        self,
        *,
        period: LeaderboardPeriod,
        limit: int,
    ) -> list[LeaderboardEntry]:
        rows = await self._repo.list_leaderboard(period=period, limit=limit)
        entries: list[LeaderboardEntry] = []
        for rank, (stats, profile_display_name) in enumerate(rows, start=1):
            points = (
                stats.week_points if period == "week" else stats.total_points
            )
            entries.append(
                LeaderboardEntry(
                    rank=rank,
                    display_name=resolve_public_display_name(
                        profile_display_name,
                        stats.student_id,
                    ),
                    points=points,
                )
            )
        return entries

    def _apply_points_to_stats(
        self,
        stats: StudentStats,
        points: int,
        event_date: date,
    ) -> None:
        if points <= 0:
            return
        self._reset_week_points_if_new_week(stats, event_date)
        stats.total_points += points
        stats.week_points += points

    def _reset_week_points_if_new_week(
        self,
        stats: StudentStats,
        event_date: date,
    ) -> None:
        if stats.week_points == 0:
            return
        marker = stats.last_active_date
        if marker is None:
            return
        if _iso_week_key(marker) != _iso_week_key(event_date):
            stats.week_points = 0

    async def _update_streak_for_new_active_day(
        self,
        stats: StudentStats,
        student_id: uuid.UUID,
        active_date: date,
    ) -> None:
        if stats.last_active_date == active_date:
            return

        if stats.last_active_date == active_date - timedelta(days=1):
            stats.current_streak += 1
        else:
            stats.current_streak = 1

        stats.longest_streak = max(stats.longest_streak, stats.current_streak)
        stats.last_active_date = active_date

        await self.record_event(
            student_id,
            ActivityEventType.STREAK_DAILY,
            active_date.isoformat(),
            POINTS_STREAK_DAILY,
            occurred_at=datetime.combine(
                active_date,
                datetime.min.time(),
                tzinfo=timezone.utc,
            ),
        )

        if stats.current_streak == 7:
            await self.record_event(
                student_id,
                ActivityEventType.STREAK_WEEKLY,
                _iso_week_key(active_date),
                POINTS_STREAK_WEEKLY,
                occurred_at=datetime.combine(
                    active_date,
                    datetime.min.time(),
                    tzinfo=timezone.utc,
                ),
            )
