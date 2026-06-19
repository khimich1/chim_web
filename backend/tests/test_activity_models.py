"""Tests for activity ledger / stats models and migration 008."""

from __future__ import annotations

import asyncio
import uuid
from datetime import date
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
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
        email="teacher@example.com",
        password_hash=hash_password("pass"),
        role=UserRole.TEACHER,
    )
    student = User(
        email="student@example.com",
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


def test_activity_event_types() -> None:
    assert {t.value for t in ActivityEventType} == {
        "step_correct",
        "homework_complete",
        "streak_daily",
        "streak_weekly",
        "onboarding_welcome_viewed",
        "onboarding_welcome_completed",
        "onboarding_welcome_skipped",
        "onboarding_checklist_step",
        "onboarding_first_action",
    }


@pytest.mark.asyncio
async def test_create_activity_event_with_step_ref(db_session, student_user) -> None:
    step_id = uuid.uuid4()
    event = StudentActivityEvent(
        student_id=student_user.id,
        event_type=ActivityEventType.STEP_CORRECT,
        ref_id=str(step_id),
        points=10,
        payload={"session_id": str(uuid.uuid4())},
    )
    db_session.add(event)
    await db_session.commit()

    loaded = await db_session.scalar(
        select(StudentActivityEvent).where(StudentActivityEvent.id == event.id)
    )
    assert loaded is not None
    assert loaded.ref_id == str(step_id)
    assert loaded.points == 10
    assert loaded.event_type == ActivityEventType.STEP_CORRECT


@pytest.mark.asyncio
async def test_create_activity_event_homework_ref(db_session, student_user) -> None:
    assignment_id = uuid.uuid4()
    event = StudentActivityEvent(
        student_id=student_user.id,
        event_type=ActivityEventType.HOMEWORK_COMPLETE,
        ref_id=str(assignment_id),
        points=50,
    )
    db_session.add(event)
    await db_session.commit()

    loaded = await db_session.scalar(
        select(StudentActivityEvent).where(
            StudentActivityEvent.ref_id == str(assignment_id)
        )
    )
    assert loaded is not None
    assert loaded.event_type == ActivityEventType.HOMEWORK_COMPLETE


@pytest.mark.asyncio
async def test_create_streak_event_with_date_ref(db_session, student_user) -> None:
    event = StudentActivityEvent(
        student_id=student_user.id,
        event_type=ActivityEventType.STREAK_DAILY,
        ref_id="2026-06-19",
        points=5,
    )
    db_session.add(event)
    await db_session.commit()

    loaded = await db_session.scalar(
        select(StudentActivityEvent).where(
            StudentActivityEvent.event_type == ActivityEventType.STREAK_DAILY
        )
    )
    assert loaded is not None
    assert loaded.ref_id == "2026-06-19"


@pytest.mark.asyncio
async def test_unique_constraint_prevents_duplicate_events(
    db_session, student_user
) -> None:
    step_id = uuid.uuid4()
    db_session.add(
        StudentActivityEvent(
            student_id=student_user.id,
            event_type=ActivityEventType.STEP_CORRECT,
            ref_id=str(step_id),
            points=10,
        )
    )
    await db_session.commit()

    db_session.add(
        StudentActivityEvent(
            student_id=student_user.id,
            event_type=ActivityEventType.STEP_CORRECT,
            ref_id=str(step_id),
            points=10,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_create_student_stats(db_session, student_user) -> None:
    stats = StudentStats(
        student_id=student_user.id,
        total_points=60,
        week_points=25,
        current_streak=3,
        longest_streak=5,
        last_active_date=date(2026, 6, 19),
        tasks_solved=4,
        total_minutes=42,
    )
    db_session.add(stats)
    await db_session.commit()

    loaded = await db_session.scalar(
        select(StudentStats).where(StudentStats.student_id == student_user.id)
    )
    assert loaded is not None
    assert loaded.total_points == 60
    assert loaded.week_points == 25
    assert loaded.current_streak == 3
    assert loaded.tasks_solved == 4
    assert loaded.last_active_date == date(2026, 6, 19)


@pytest.mark.asyncio
async def test_student_profile_display_name(db_session, student_user) -> None:
    profile = await db_session.scalar(
        select(StudentProfile).where(StudentProfile.user_id == student_user.id)
    )
    assert profile is not None
    assert profile.display_name == "Химик-42"


def test_alembic_upgrade_creates_activity_tables(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_file = tmp_path / "alembic_activity.db"
    url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")
    get_settings.cache_clear()

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    async def _assert_schema() -> None:
        engine = create_async_engine(url)
        async with engine.connect() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
            columns = await conn.run_sync(
                lambda sync_conn: {
                    col["name"]
                    for col in inspect(sync_conn).get_columns("student_profiles")
                }
            )
            event_uniques = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_unique_constraints(
                    "student_activity_events"
                )
            )
        await engine.dispose()

        assert "student_activity_events" in tables
        assert "student_stats" in tables
        assert "display_name" in columns
        unique_names = {u["name"] for u in event_uniques}
        assert "uq_activity_event_student_type_ref" in unique_names

    asyncio.run(_assert_schema())


def test_alembic_downgrade_drops_activity_tables(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_file = tmp_path / "alembic_activity_down.db"
    url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")
    get_settings.cache_clear()

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "007_rag_embeddings")

    async def _assert_dropped() -> None:
        engine = create_async_engine(url)
        async with engine.connect() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
            columns = await conn.run_sync(
                lambda sync_conn: {
                    col["name"]
                    for col in inspect(sync_conn).get_columns("student_profiles")
                }
            )
        await engine.dispose()
        assert "student_activity_events" not in tables
        assert "student_stats" not in tables
        assert "display_name" not in columns

    asyncio.run(_assert_dropped())
