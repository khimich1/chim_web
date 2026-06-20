"""Tests for TeacherTheme, CustomTask, and extended TestSession models."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.base import Base
from app.models import (
    CustomTask,
    ExamTrack,
    GradingMode,
    StepStatus,
    TeacherTheme,
    TestSession,
    TestSessionSource,
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
async def test_teacher_theme_with_custom_tasks(db_session) -> None:
    teacher = User(
        email="teacher@example.com",
        password_hash=hash_password("pass"),
        role=UserRole.TEACHER,
    )
    db_session.add(teacher)
    await db_session.flush()

    theme = TeacherTheme(
        teacher_id=teacher.id,
        title="ОВР",
        description="Окислительно-восстановительные реакции",
        is_published=True,
        sort_order=1,
        tasks=[
            CustomTask(
                title="Задание 1",
                sort_order=0,
                grading_mode=GradingMode.AUTO,
                question_blocks=[{"type": "text", "content": "2+2=?"}],
                correct_value="4",
            ),
            CustomTask(
                title="Задание 2",
                sort_order=1,
                grading_mode=GradingMode.SELF_CHECK,
                question_blocks=[{"type": "text", "content": "Опишите ОВР"}],
                reference_answer=[{"type": "text", "content": "Эталон"}],
            ),
        ],
    )
    db_session.add(theme)
    await db_session.commit()

    loaded = await db_session.scalar(
        select(TeacherTheme).where(TeacherTheme.id == theme.id)
    )
    assert loaded is not None
    assert loaded.teacher_id == teacher.id
    assert loaded.is_published is True
    assert len(loaded.tasks) == 2
    assert loaded.tasks[0].grading_mode == GradingMode.AUTO
    assert loaded.tasks[1].reference_answer[0]["content"] == "Эталон"


@pytest.mark.asyncio
async def test_custom_test_session_with_custom_task_step(db_session) -> None:
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

    theme = TeacherTheme(teacher_id=teacher.id, title="Тема", is_published=True)
    db_session.add(theme)
    await db_session.flush()

    task_id = uuid.uuid4()
    task = CustomTask(
        id=task_id,
        theme_id=theme.id,
        grading_mode=GradingMode.AUTO,
        question_blocks=[{"type": "text", "content": "H2O?"}],
        correct_value="вода",
    )
    db_session.add(task)
    await db_session.flush()

    session = TestSession(
        student_id=student.id,
        track=ExamTrack.EGE,
        variant_ref=None,
        source=TestSessionSource.CUSTOM,
        custom_theme_id=theme.id,
        custom_task_ids=[str(task_id)],
        status=TestSessionStatus.IN_PROGRESS,
        steps=[
            TestSessionStep(
                position=0,
                custom_task_id=task_id,
                status=StepStatus.UNSEEN,
            ),
        ],
    )
    db_session.add(session)
    await db_session.commit()

    loaded = await db_session.scalar(
        select(TestSession).where(TestSession.id == session.id)
    )
    assert loaded is not None
    assert loaded.source == TestSessionSource.CUSTOM
    assert loaded.custom_theme_id == theme.id
    assert loaded.custom_task_ids == [str(task_id)]
    assert len(loaded.steps) == 1
    assert loaded.steps[0].test_id is None
    assert loaded.steps[0].custom_task_id == task_id


@pytest.mark.asyncio
async def test_exam_session_step_still_uses_test_id(db_session) -> None:
    student = User(
        email="student@example.com",
        password_hash=hash_password("pass"),
        role=UserRole.STUDENT,
    )
    db_session.add(student)
    await db_session.flush()

    session = TestSession(
        student_id=student.id,
        track=ExamTrack.OGE,
        variant_ref="001.txt",
        source=TestSessionSource.EXAM,
        status=TestSessionStatus.IN_PROGRESS,
        steps=[
            TestSessionStep(position=0, test_id=42, status=StepStatus.UNSEEN),
        ],
    )
    db_session.add(session)
    await db_session.commit()

    loaded = await db_session.scalar(
        select(TestSession).where(TestSession.id == session.id)
    )
    assert loaded is not None
    assert loaded.source == TestSessionSource.EXAM
    assert loaded.steps[0].test_id == 42
    assert loaded.steps[0].custom_task_id is None
