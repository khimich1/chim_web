"""Tests for HomeworkAssignment / HomeworkSubmission models."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.base import Base
from app.models import (
    HomeworkAssignment,
    HomeworkStatus,
    HomeworkSubmission,
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
async def test_create_homework_assignment_with_submission(db_session) -> None:
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

    assignment = HomeworkAssignment(
        student_id=student.id,
        teacher_id=teacher.id,
        title="Прочитать тему",
        description="Алканы",
        items=[{"kind": "lecture", "topic": "Алканы"}],
        status=HomeworkStatus.ASSIGNED,
    )
    db_session.add(assignment)
    await db_session.flush()

    submission = HomeworkSubmission(assignment_id=assignment.id)
    db_session.add(submission)
    await db_session.commit()

    loaded = await db_session.scalar(
        select(HomeworkAssignment).where(HomeworkAssignment.id == assignment.id)
    )
    assert loaded is not None
    assert loaded.status == HomeworkStatus.ASSIGNED
    assert loaded.items[0]["kind"] == "lecture"
    assert loaded.due_at is None
