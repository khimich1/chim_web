"""Tests for TestSession / TestSessionStep models and migration 002."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.models import (
    ExamTrack,
    StepStatus,
    TestSession,
    TestSessionStatus,
    TestSessionStep,
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


@pytest.mark.asyncio
async def test_create_session_with_steps(db_session) -> None:
    student = User(
        email="student@example.com",
        password_hash=hash_password("pass"),
        role=UserRole.STUDENT,
    )
    db_session.add(student)
    await db_session.flush()

    session = TestSession(
        student_id=student.id,
        track=ExamTrack.EGE,
        variant_ref="001.txt",
        status=TestSessionStatus.IN_PROGRESS,
        steps=[
            TestSessionStep(position=0, test_id=11, status=StepStatus.UNSEEN),
            TestSessionStep(position=1, test_id=12, status=StepStatus.UNSEEN),
        ],
    )
    db_session.add(session)
    await db_session.commit()

    loaded = await db_session.scalar(
        select(TestSession).where(TestSession.id == session.id)
    )
    assert loaded is not None
    assert loaded.status == TestSessionStatus.IN_PROGRESS
    assert loaded.homework_assignment_id is None
    assert len(loaded.steps) == 2
    assert [step.position for step in loaded.steps] == [0, 1]
    assert loaded.steps[0].hint_used is False
    assert loaded.steps[0].is_correct is None


def test_step_statuses() -> None:
    assert {s.value for s in StepStatus} == {"unseen", "answered", "checked"}


def test_session_statuses() -> None:
    assert {s.value for s in TestSessionStatus} == {"in_progress", "completed"}


def test_alembic_upgrade_creates_session_tables(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_file = tmp_path / "alembic_sessions.db"
    url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")
    get_settings.cache_clear()

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    async def _assert_tables() -> None:
        engine = create_async_engine(url)
        async with engine.connect() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        await engine.dispose()
        assert "test_sessions" in tables
        assert "test_session_steps" in tables

    asyncio.run(_assert_tables())
