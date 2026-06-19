"""Tests for ActivityService: idempotency, streak, week_points (Task 59)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.base import Base
from app.models import (
    ActivityEventType,
    ExamTrack,
    StudentActivityEvent,
    StudentProfile,
    StudentStats,
    User,
    UserRole,
)
from app.services.activity_service import (
    POINTS_STREAK_DAILY,
    POINTS_STREAK_WEEKLY,
    POINTS_STEP_CORRECT,
    ActivityService,
)


@pytest.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def student_user(db_session):
    teacher = User(
        email="teacher-activity@example.com",
        password_hash=hash_password("pass"),
        role=UserRole.TEACHER,
    )
    student = User(
        email="student-activity@example.com",
        password_hash=hash_password("pass"),
        role=UserRole.STUDENT,
    )
    db_session.add_all([teacher, student])
    await db_session.flush()

    profile = StudentProfile(
        user_id=student.id,
        teacher_id=teacher.id,
        track=ExamTrack.EGE,
        display_name="Химик-42",
    )
    db_session.add(profile)
    await db_session.flush()
    return student


def _utc_dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, 12, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_record_step_correct_awards_points_and_tasks_solved(
    db_session, student_user
) -> None:
    service = ActivityService(db_session)
    step_id = uuid.uuid4()
    when = _utc_dt(2026, 6, 19)

    result = await service.record_step_correct(
        student_user.id,
        step_id,
        occurred_at=when,
    )
    await db_session.commit()

    assert result.created is True
    assert result.points_awarded == POINTS_STEP_CORRECT

    stats = await db_session.get(StudentStats, student_user.id)
    assert stats is not None
    assert stats.total_points == POINTS_STEP_CORRECT + POINTS_STREAK_DAILY
    assert stats.tasks_solved == 1
    assert stats.current_streak == 1
    assert stats.last_active_date == date(2026, 6, 19)


@pytest.mark.asyncio
async def test_record_step_correct_is_idempotent(db_session, student_user) -> None:
    service = ActivityService(db_session)
    step_id = uuid.uuid4()
    when = _utc_dt(2026, 6, 19)

    first = await service.record_step_correct(
        student_user.id, step_id, occurred_at=when
    )
    second = await service.record_step_correct(
        student_user.id, step_id, occurred_at=when
    )
    await db_session.commit()

    assert first.created is True
    assert second.created is False
    assert second.points_awarded == 0

    stats = await db_session.get(StudentStats, student_user.id)
    assert stats is not None
    assert stats.tasks_solved == 1
    assert stats.total_points == POINTS_STEP_CORRECT + POINTS_STREAK_DAILY

    count = await db_session.scalar(
        select(func.count())
        .select_from(StudentActivityEvent)
        .where(
            StudentActivityEvent.student_id == student_user.id,
            StudentActivityEvent.event_type == ActivityEventType.STEP_CORRECT,
        )
    )
    assert count == 1


@pytest.mark.asyncio
async def test_same_day_multiple_steps_one_daily_streak_bonus(
    db_session, student_user
) -> None:
    service = ActivityService(db_session)
    when = _utc_dt(2026, 6, 19)

    await service.record_step_correct(
        student_user.id, uuid.uuid4(), occurred_at=when
    )
    await service.record_step_correct(
        student_user.id, uuid.uuid4(), occurred_at=when + timedelta(hours=2)
    )
    await db_session.commit()

    stats = await db_session.get(StudentStats, student_user.id)
    assert stats is not None
    assert stats.tasks_solved == 2
    assert stats.current_streak == 1
    assert stats.total_points == 2 * POINTS_STEP_CORRECT + POINTS_STREAK_DAILY

    daily_count = await db_session.scalar(
        select(func.count())
        .select_from(StudentActivityEvent)
        .where(
            StudentActivityEvent.event_type == ActivityEventType.STREAK_DAILY,
            StudentActivityEvent.student_id == student_user.id,
        )
    )
    assert daily_count == 1


@pytest.mark.asyncio
async def test_streak_increments_on_consecutive_days(db_session, student_user) -> None:
    service = ActivityService(db_session)

    await service.record_step_correct(
        student_user.id,
        uuid.uuid4(),
        occurred_at=_utc_dt(2026, 6, 17),
    )
    await service.record_step_correct(
        student_user.id,
        uuid.uuid4(),
        occurred_at=_utc_dt(2026, 6, 18),
    )
    await db_session.commit()

    stats = await db_session.get(StudentStats, student_user.id)
    assert stats is not None
    assert stats.current_streak == 2
    assert stats.longest_streak == 2
    assert stats.last_active_date == date(2026, 6, 18)


@pytest.mark.asyncio
async def test_streak_resets_after_gap(db_session, student_user) -> None:
    service = ActivityService(db_session)

    await service.record_step_correct(
        student_user.id,
        uuid.uuid4(),
        occurred_at=_utc_dt(2026, 6, 15),
    )
    await service.record_step_correct(
        student_user.id,
        uuid.uuid4(),
        occurred_at=_utc_dt(2026, 6, 17),
    )
    await db_session.commit()

    stats = await db_session.get(StudentStats, student_user.id)
    assert stats is not None
    assert stats.current_streak == 1
    assert stats.longest_streak == 1


@pytest.mark.asyncio
async def test_streak_weekly_bonus_on_seventh_consecutive_day(
    db_session, student_user
) -> None:
    service = ActivityService(db_session)
    start = date(2026, 6, 13)

    for offset in range(7):
        await service.record_step_correct(
            student_user.id,
            uuid.uuid4(),
            occurred_at=datetime.combine(
                start + timedelta(days=offset),
                datetime.min.time(),
                tzinfo=timezone.utc,
            ),
        )
    await db_session.commit()

    stats = await db_session.get(StudentStats, student_user.id)
    assert stats is not None
    assert stats.current_streak == 7
    assert stats.longest_streak == 7
    assert stats.tasks_solved == 7

    expected_points = (
        7 * POINTS_STEP_CORRECT
        + 7 * POINTS_STREAK_DAILY
        + POINTS_STREAK_WEEKLY
    )
    assert stats.total_points == expected_points

    weekly = await db_session.scalar(
        select(StudentActivityEvent).where(
            StudentActivityEvent.student_id == student_user.id,
            StudentActivityEvent.event_type == ActivityEventType.STREAK_WEEKLY,
        )
    )
    assert weekly is not None
    assert weekly.ref_id == "2026-W25"
    assert weekly.points == POINTS_STREAK_WEEKLY


@pytest.mark.asyncio
async def test_streak_weekly_not_awarded_again_on_day_eight(
    db_session, student_user
) -> None:
    """Day 8 of a continuing streak does not grant a second +30 bonus."""
    service = ActivityService(db_session)
    start = date(2026, 6, 13)

    for offset in range(8):
        await service.record_step_correct(
            student_user.id,
            uuid.uuid4(),
            occurred_at=datetime.combine(
                start + timedelta(days=offset),
                datetime.min.time(),
                tzinfo=timezone.utc,
            ),
        )
    await db_session.commit()

    weekly_count = await db_session.scalar(
        select(func.count())
        .select_from(StudentActivityEvent)
        .where(
            StudentActivityEvent.student_id == student_user.id,
            StudentActivityEvent.event_type == ActivityEventType.STREAK_WEEKLY,
        )
    )
    assert weekly_count == 1


@pytest.mark.asyncio
async def test_week_points_accumulates_within_calendar_week(
    db_session, student_user
) -> None:
    service = ActivityService(db_session)

    await service.record_step_correct(
        student_user.id,
        uuid.uuid4(),
        occurred_at=_utc_dt(2026, 6, 16),
    )
    await service.record_step_correct(
        student_user.id,
        uuid.uuid4(),
        occurred_at=_utc_dt(2026, 6, 18),
    )
    await db_session.commit()

    stats = await db_session.get(StudentStats, student_user.id)
    assert stats is not None
    assert stats.week_points == 2 * POINTS_STEP_CORRECT + 2 * POINTS_STREAK_DAILY


@pytest.mark.asyncio
async def test_week_points_resets_on_new_calendar_week(
    db_session, student_user
) -> None:
    service = ActivityService(db_session)

    await service.record_step_correct(
        student_user.id,
        uuid.uuid4(),
        occurred_at=_utc_dt(2026, 6, 20),
    )
    await service.record_step_correct(
        student_user.id,
        uuid.uuid4(),
        occurred_at=_utc_dt(2026, 6, 23),
    )
    await db_session.commit()

    stats = await db_session.get(StudentStats, student_user.id)
    assert stats is not None
    # 2026-06-20 is W25; 2026-06-23 is W26 — week_points only from the new week
    assert stats.week_points == POINTS_STEP_CORRECT + POINTS_STREAK_DAILY
    assert stats.total_points == (
        2 * POINTS_STEP_CORRECT + 2 * POINTS_STREAK_DAILY
    )


@pytest.mark.asyncio
async def test_add_session_minutes_updates_total(db_session, student_user) -> None:
    service = ActivityService(db_session)

    stats_read = await service.add_session_minutes(student_user.id, 15)
    await service.add_session_minutes(student_user.id, 10)
    await db_session.commit()

    assert stats_read.total_minutes == 15

    stats = await db_session.get(StudentStats, student_user.id)
    assert stats is not None
    assert stats.total_minutes == 25
    assert stats.total_points == 0


@pytest.mark.asyncio
async def test_streak_increments_across_utc_midnight(
    db_session, student_user
) -> None:
    """Late-night UTC activity on day N and early-morning on N+1 counts as consecutive."""
    service = ActivityService(db_session)

    await service.record_step_correct(
        student_user.id,
        uuid.uuid4(),
        occurred_at=datetime(2026, 6, 18, 23, 59, tzinfo=timezone.utc),
    )
    await service.record_step_correct(
        student_user.id,
        uuid.uuid4(),
        occurred_at=datetime(2026, 6, 19, 0, 1, tzinfo=timezone.utc),
    )
    await db_session.commit()

    stats = await db_session.get(StudentStats, student_user.id)
    assert stats is not None
    assert stats.current_streak == 2
    assert stats.last_active_date == date(2026, 6, 19)


@pytest.mark.asyncio
async def test_week_points_reset_at_iso_week_boundary_utc_midnight(
    db_session, student_user
) -> None:
    """week_points resets when the next event falls in a new ISO week (UTC midnight rollover)."""
    service = ActivityService(db_session)

    await service.record_step_correct(
        student_user.id,
        uuid.uuid4(),
        occurred_at=datetime(2026, 6, 21, 23, 59, tzinfo=timezone.utc),
    )
    await service.record_step_correct(
        student_user.id,
        uuid.uuid4(),
        occurred_at=datetime(2026, 6, 22, 0, 1, tzinfo=timezone.utc),
    )
    await db_session.commit()

    stats = await db_session.get(StudentStats, student_user.id)
    assert stats is not None
    # 2026-06-21 is W25; 2026-06-22 is W26 — only the Monday event counts toward week_points
    assert stats.week_points == POINTS_STEP_CORRECT + POINTS_STREAK_DAILY
    assert stats.total_points == (
        2 * POINTS_STEP_CORRECT + 2 * POINTS_STREAK_DAILY
    )


@pytest.mark.asyncio
async def test_record_event_duplicate_returns_not_created(
    db_session, student_user
) -> None:
    service = ActivityService(db_session)
    ref = str(uuid.uuid4())

    first = await service.record_event(
        student_user.id,
        ActivityEventType.HOMEWORK_COMPLETE,
        ref,
        50,
    )
    second = await service.record_event(
        student_user.id,
        ActivityEventType.HOMEWORK_COMPLETE,
        ref,
        50,
    )
    await db_session.commit()

    assert first.created is True
    assert first.points_awarded == 50
    assert second.created is False

    stats = await db_session.get(StudentStats, student_user.id)
    assert stats is not None
    assert stats.total_points == 50
