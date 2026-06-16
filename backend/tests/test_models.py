"""Tests for User / StudentProfile models, migrations, and seed CLI."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.cli.seed_teacher import seed_teacher
from app.core.config import get_settings
from app.core.security import verify_password
from app.db.base import Base
from app.models import ExamTrack, StudentProfile, User, UserRole


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
async def test_create_teacher_user(db_session) -> None:
    teacher = User(
        email="teacher@example.com",
        password_hash="hashed",
        role=UserRole.TEACHER,
    )
    db_session.add(teacher)
    await db_session.commit()
    await db_session.refresh(teacher)

    assert teacher.id is not None
    assert teacher.role == UserRole.TEACHER
    assert teacher.is_active is True


@pytest.mark.asyncio
async def test_create_student_with_profile(db_session) -> None:
    teacher = User(
        email="teacher@example.com",
        password_hash="hashed",
        role=UserRole.TEACHER,
    )
    student_user = User(
        email="student@example.com",
        password_hash="hashed",
        role=UserRole.STUDENT,
    )
    db_session.add_all([teacher, student_user])
    await db_session.flush()

    profile = StudentProfile(
        user_id=student_user.id,
        teacher_id=teacher.id,
        track=ExamTrack.EGE,
    )
    db_session.add(profile)
    await db_session.commit()

    loaded = await db_session.scalar(
        select(StudentProfile).where(StudentProfile.user_id == student_user.id)
    )
    assert loaded is not None
    assert loaded.track == ExamTrack.EGE
    assert loaded.teacher_id == teacher.id


def test_user_roles_are_teacher_or_student() -> None:
    assert {role.value for role in UserRole} == {"teacher", "student"}


def test_exam_tracks_are_ege_or_oge() -> None:
    assert {track.value for track in ExamTrack} == {"ege", "oge"}


@pytest.mark.asyncio
async def test_seed_teacher_creates_hashed_password(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_file = tmp_path / "seed.db"
    url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()

    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

    teacher = await seed_teacher("teacher@example.com", "secret-pass")
    assert teacher.role == UserRole.TEACHER
    assert verify_password("secret-pass", teacher.password_hash)


def test_alembic_upgrade_head_creates_tables(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_file = tmp_path / "alembic.db"
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
        assert "users" in tables
        assert "student_profiles" in tables

    asyncio.run(_assert_tables())


def test_alembic_reads_url_from_settings_not_ini_placeholder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: env.py must pull DATABASE_URL from Settings.

    The alembic.ini `sqlalchemy.url` is blank on purpose; if a non-empty
    placeholder (e.g. `driver://...`) is reintroduced, env.py would stop
    falling back to Settings and `command.upgrade` would raise
    NoSuchModuleError. This test fails loudly in that case.
    """
    db_file = tmp_path / "from_settings.db"
    url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")
    get_settings.cache_clear()

    # Intentionally do NOT set sqlalchemy.url — env.py must inject it.
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")

    assert db_file.exists()
