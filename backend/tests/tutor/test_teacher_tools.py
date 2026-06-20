"""Tests for teacher tutor tools service and LangGraph tool wiring (Task 45)."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.security import hash_password
from app.db.base import Base
from app.models import (
    ExamTrack,
    HomeworkAssignment,
    HomeworkStatus,
    StepStatus,
    StudentProfile,
    TestSession,
    TestSessionStatus,
    TestSessionStep,
    User,
    UserRole,
)
from app.models.enums import HomeworkItemKind
from app.models.homework import HomeworkItemProgress
from app.services.tutor.context import TutorRunContext
from app.services.tutor.teacher_tools import TeacherTutorToolsService
from app.services.tutor.tools import build_tools


def test_teacher_tools_registered_only_for_teacher_with_backend() -> None:
    student_ctx = TutorRunContext(
        track="ege",
        user_id="u1",
        role="student",
        run_async=lambda coro: asyncio.run(coro),
        student_tools_service=MagicMock(),
    )
    teacher_ctx = TutorRunContext(
        track="ege",
        user_id="t1",
        role="teacher",
        run_async=lambda coro: asyncio.run(coro),
        teacher_tools_service=MagicMock(),
    )
    student_names = {tool.name for tool in build_tools(student_ctx)}
    teacher_names = {tool.name for tool in build_tools(teacher_ctx)}

    assert "summarize_student" not in student_names
    assert {"summarize_student", "suggest_homework", "class_overview"} <= teacher_names
    assert "get_my_homework" not in teacher_names


def test_summarize_student_tool_returns_error_for_foreign_student() -> None:
    service = MagicMock()
    service.summarize_student = AsyncMock(return_value=None)

    ctx = TutorRunContext(
        track="ege",
        user_id="t1",
        role="teacher",
        run_async=lambda coro: asyncio.run(coro),
        teacher_tools_service=service,
    )
    tool = next(t for t in build_tools(ctx) if t.name == "summarize_student")
    payload = json.loads(tool.invoke({"student_id": str(uuid.uuid4())}))

    assert "error" in payload
    service.summarize_student.assert_awaited_once()


def test_suggest_homework_tool_returns_draft_json() -> None:
    student_id = uuid.uuid4()
    service = MagicMock()
    draft = MagicMock()
    draft.model_dump.return_value = {
        "student_id": str(student_id),
        "title": "Повторение: Алканы",
        "items": [{"kind": "lecture", "topic": "Алканы"}],
        "is_draft": True,
    }
    service.suggest_homework = AsyncMock(return_value=draft)

    ctx = TutorRunContext(
        track="ege",
        user_id="t1",
        role="teacher",
        run_async=lambda coro: asyncio.run(coro),
        teacher_tools_service=service,
    )
    tool = next(t for t in build_tools(ctx) if t.name == "suggest_homework")
    payload = json.loads(tool.invoke({"student_id": str(student_id)}))

    assert payload["is_draft"] is True
    assert payload["items"][0]["kind"] == "lecture"
    service.suggest_homework.assert_awaited_once_with(student_id)


@pytest.fixture
async def teacher_tools_env(tmp_path: Path, rag_content_dbs: dict[str, Path]):
    db_file = tmp_path / "teacher_tools.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    foreign_student_id = uuid.uuid4()
    foreign_teacher_id = uuid.uuid4()

    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        session.add_all(
            [
                User(
                    id=teacher_id,
                    email="teacher@example.com",
                    password_hash=hash_password("pass"),
                    role=UserRole.TEACHER,
                ),
                User(
                    id=foreign_teacher_id,
                    email="other-teacher@example.com",
                    password_hash=hash_password("pass"),
                    role=UserRole.TEACHER,
                ),
                User(
                    id=student_id,
                    email="student@example.com",
                    password_hash=hash_password("pass"),
                    role=UserRole.STUDENT,
                ),
                User(
                    id=foreign_student_id,
                    email="foreign@example.com",
                    password_hash=hash_password("pass"),
                    role=UserRole.STUDENT,
                ),
            ]
        )
        await session.flush()
        session.add_all(
            [
                StudentProfile(
                    user_id=student_id,
                    teacher_id=teacher_id,
                    track=ExamTrack.EGE,
                ),
                StudentProfile(
                    user_id=foreign_student_id,
                    teacher_id=foreign_teacher_id,
                    track=ExamTrack.EGE,
                ),
            ]
        )

        session.add(
            HomeworkAssignment(
                student_id=student_id,
                teacher_id=teacher_id,
                title="Сданное ДЗ",
                items=[{"kind": "lecture", "topic": "Алканы"}],
                status=HomeworkStatus.SUBMITTED,
                item_progress=[
                    HomeworkItemProgress(
                        item_index=0,
                        kind=HomeworkItemKind.LECTURE,
                        completed=True,
                    )
                ],
            )
        )

        session.add_all(
            [
                TestSession(
                    student_id=student_id,
                    track=ExamTrack.EGE,
                    variant_ref="001.txt",
                    status=TestSessionStatus.COMPLETED,
                    steps=[
                        TestSessionStep(
                            position=0,
                            test_id=1,
                            answer="wrong",
                            is_correct=False,
                            status=StepStatus.CHECKED,
                            checked_at=datetime.now(timezone.utc),
                        ),
                    ],
                ),
                TestSession(
                    student_id=foreign_student_id,
                    track=ExamTrack.EGE,
                    variant_ref="001.txt",
                    status=TestSessionStatus.COMPLETED,
                    steps=[
                        TestSessionStep(
                            position=0,
                            test_id=1,
                            answer="foreign",
                            is_correct=False,
                            status=StepStatus.CHECKED,
                            checked_at=datetime.now(timezone.utc),
                        ),
                    ],
                ),
            ]
        )
        await session.commit()

        teacher = await session.get(User, teacher_id)
        assert teacher is not None

        settings = Settings(
            database_url=db_url,
            jwt_secret="test-secret",
            content_ege_db_path=rag_content_dbs["ege"],
            content_oge_db_path=rag_content_dbs["oge"],
            content_lectures_db_path=rag_content_dbs["lectures"],
        )

        yield {
            "session": session,
            "teacher": teacher,
            "student_id": student_id,
            "foreign_student_id": foreign_student_id,
            "settings": settings,
            "session_maker": session_maker,
        }

    await engine.dispose()


@pytest.mark.asyncio
async def test_summarize_student_service_scoped_to_teacher(
    teacher_tools_env,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.tutor.student_tools.get_settings",
        lambda: teacher_tools_env["settings"],
    )
    monkeypatch.setattr(
        "app.services.tutor.tasks.get_settings",
        lambda: teacher_tools_env["settings"],
    )

    service = TeacherTutorToolsService(
        teacher_tools_env["session"],
        user=teacher_tools_env["teacher"],
    )
    summary = await service.summarize_student(teacher_tools_env["student_id"])
    foreign = await service.summarize_student(teacher_tools_env["foreign_student_id"])

    assert summary is not None
    assert summary.email == "student@example.com"
    assert summary.total_incorrect_steps == 1
    assert summary.activity.submitted_homework == 1
    assert foreign is None


@pytest.mark.asyncio
async def test_suggest_homework_does_not_persist_assignment(
    teacher_tools_env,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.tutor.student_tools.get_settings",
        lambda: teacher_tools_env["settings"],
    )
    monkeypatch.setattr(
        "app.services.tutor.tasks.get_settings",
        lambda: teacher_tools_env["settings"],
    )

    session = teacher_tools_env["session"]
    before = await session.scalar(select(func.count()).select_from(HomeworkAssignment))

    service = TeacherTutorToolsService(session, user=teacher_tools_env["teacher"])
    draft = await service.suggest_homework(teacher_tools_env["student_id"])

    after = await session.scalar(select(func.count()).select_from(HomeworkAssignment))

    assert draft is not None
    assert draft.is_draft is True
    assert draft.items
    assert before == after


@pytest.mark.asyncio
async def test_class_overview_aggregates_without_personal_answers(
    teacher_tools_env,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.tutor.student_tools.get_settings",
        lambda: teacher_tools_env["settings"],
    )
    monkeypatch.setattr(
        "app.services.tutor.tasks.get_settings",
        lambda: teacher_tools_env["settings"],
    )

    service = TeacherTutorToolsService(
        teacher_tools_env["session"],
        user=teacher_tools_env["teacher"],
    )
    overview = await service.class_overview()
    payload = overview.model_dump(mode="json")

    assert overview.total_students == 1
    assert overview.total_incorrect_steps == 1
    assert overview.by_type
    assert overview.by_type[0].task_type == 15
    assert "foreign" not in json.dumps(payload)
    assert "answer" not in json.dumps(payload).lower()
