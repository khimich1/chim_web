"""Shared fixtures for direct async service unit tests (accurate coverage)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.security import hash_password
from app.db.base import Base
from app.models import ExamTrack, StudentProfile, User, UserRole
from tests.content.conftest import _create_tests_db


@pytest.fixture
def content_ege_db(tmp_path: Path) -> Path:
    path = tmp_path / "test_ege.db"
    _create_tests_db(path, with_bug=True)
    return path


@pytest.fixture
def service_settings(content_ege_db: Path) -> Settings:
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="test-jwt-secret-at-least-32-bytes-long",
        CONTENT_EGE_DB_PATH=str(content_ege_db),
        CONTENT_OGE_DB_PATH=str(content_ege_db),
    )


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def teacher_student_users(
    db_session: AsyncSession,
) -> tuple[User, User, User]:
    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    other_student_id = uuid.uuid4()
    teacher = User(
        id=teacher_id,
        email="teacher@example.com",
        password_hash=hash_password("secret"),
        role=UserRole.TEACHER,
    )
    student = User(
        id=student_id,
        email="student@example.com",
        password_hash=hash_password("secret"),
        role=UserRole.STUDENT,
    )
    other = User(
        id=other_student_id,
        email="other@example.com",
        password_hash=hash_password("secret"),
        role=UserRole.STUDENT,
    )
    db_session.add_all([teacher, student, other])
    await db_session.flush()
    db_session.add_all(
        [
            StudentProfile(
                user_id=student_id,
                teacher_id=teacher_id,
                track=ExamTrack.EGE,
            ),
            StudentProfile(
                user_id=other_student_id,
                teacher_id=teacher_id,
                track=ExamTrack.EGE,
            ),
        ]
    )
    await db_session.commit()
    return teacher, student, other
