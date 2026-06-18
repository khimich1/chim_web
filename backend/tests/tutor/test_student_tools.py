"""Tests for student tutor tools service and LangGraph tool wiring (Task 43)."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.security import hash_password
from app.db.base import Base
from app.models import (
    ExamTrack,
    HomeworkAssignment,
    HomeworkItemProgress,
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
from app.repositories.app.test_session_repo import TestSessionRepository
from app.services.tutor.context import TutorRunContext
from app.services.tutor.student_tools import StudentTutorToolsService
from app.services.tutor.tools import build_tools
from app.services.tutor.type_topic_map import resolve_topic_for_type


def test_resolve_topic_prefers_available_textbook_topic() -> None:
    topic = resolve_topic_for_type(
        "ege",
        15,
        available_topics={"Алканы", "Соли"},
    )
    assert topic == "Алканы"


def test_student_tools_registered_only_for_student_with_backend() -> None:
    student_ctx = TutorRunContext(
        track="ege",
        user_id="u1",
        role="student",
        run_async=lambda coro: asyncio.run(coro),
        student_tools_service=MagicMock(),
    )
    teacher_ctx = TutorRunContext(track="ege", user_id="t1", role="teacher")
    student_names = {tool.name for tool in build_tools(student_ctx)}
    teacher_names = {tool.name for tool in build_tools(teacher_ctx)}

    assert {"get_my_homework", "analyze_my_mistakes", "recommend_topics"} <= student_names
    assert {"generate_practice", "get_selfcheck"} <= student_names
    assert "get_my_homework" not in teacher_names


def test_get_my_homework_tool_returns_json() -> None:
    service = MagicMock()
    item = MagicMock()
    item.model_dump.return_value = {
        "id": str(uuid.uuid4()),
        "title": "ДЗ 1",
        "status": "assigned",
    }
    service.get_my_homework = AsyncMock(return_value=[item])

    ctx = TutorRunContext(
        track="ege",
        user_id="u1",
        role="student",
        run_async=lambda coro: asyncio.run(coro),
        student_tools_service=service,
    )
    tool = next(t for t in build_tools(ctx) if t.name == "get_my_homework")
    payload = json.loads(tool.invoke({}))

    assert len(payload) == 1
    assert payload[0]["title"] == "ДЗ 1"
    service.get_my_homework.assert_awaited_once()


def test_analyze_my_mistakes_excludes_active_session_in_tool() -> None:
    active_id = uuid.uuid4()
    service = MagicMock()
    analysis = MagicMock()
    analysis.model_dump.return_value = {"total_incorrect_steps": 2, "by_type": []}
    service.analyze_my_mistakes = AsyncMock(return_value=analysis)

    ctx = TutorRunContext(
        track="ege",
        user_id="u1",
        role="student",
        active_test_session_id=active_id,
        run_async=lambda coro: asyncio.run(coro),
        student_tools_service=service,
    )
    tool = next(t for t in build_tools(ctx) if t.name == "analyze_my_mistakes")
    tool.invoke({"limit": 10})

    service.analyze_my_mistakes.assert_awaited_once_with(
        limit=10,
        exclude_active_session_id=active_id,
    )


@pytest.fixture
async def student_tools_env(tmp_path: Path, rag_content_dbs: dict[str, Path]):
    db_file = tmp_path / "student_tools.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    other_student_id = uuid.uuid4()

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
                    id=student_id,
                    email="student@example.com",
                    password_hash=hash_password("pass"),
                    role=UserRole.STUDENT,
                ),
                User(
                    id=other_student_id,
                    email="other@example.com",
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
                    user_id=other_student_id,
                    teacher_id=teacher_id,
                    track=ExamTrack.EGE,
                ),
            ]
        )

        active_hw = HomeworkAssignment(
            student_id=student_id,
            teacher_id=teacher_id,
            title="Активное ДЗ",
            items=[{"kind": "lecture", "topic": "Алканы"}],
            status=HomeworkStatus.ASSIGNED,
            item_progress=[
                HomeworkItemProgress(
                    item_index=0,
                    kind=HomeworkItemKind.LECTURE,
                    completed=False,
                )
            ],
        )
        submitted_hw = HomeworkAssignment(
            student_id=student_id,
            teacher_id=teacher_id,
            title="Сданное ДЗ",
            items=[{"kind": "lecture", "topic": "Соли"}],
            status=HomeworkStatus.SUBMITTED,
            item_progress=[
                HomeworkItemProgress(
                    item_index=0,
                    kind=HomeworkItemKind.LECTURE,
                    completed=True,
                )
            ],
        )
        session.add_all([active_hw, submitted_hw])

        completed_session = TestSession(
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
        )
        active_session = TestSession(
            student_id=student_id,
            track=ExamTrack.EGE,
            variant_ref="002.txt",
            status=TestSessionStatus.IN_PROGRESS,
            steps=[
                TestSessionStep(
                    position=0,
                    test_id=1,
                    answer="also-wrong",
                    is_correct=False,
                    status=StepStatus.CHECKED,
                    checked_at=datetime.now(timezone.utc),
                ),
            ],
        )
        other_session = TestSession(
            student_id=other_student_id,
            track=ExamTrack.EGE,
            variant_ref="001.txt",
            status=TestSessionStatus.COMPLETED,
            steps=[
                TestSessionStep(
                    position=0,
                    test_id=1,
                    answer="x",
                    is_correct=False,
                    status=StepStatus.CHECKED,
                    checked_at=datetime.now(timezone.utc),
                ),
            ],
        )
        session.add_all([completed_session, active_session, other_session])
        await session.commit()

        student = await session.get(User, student_id)
        assert student is not None

        settings = Settings(
            database_url=db_url,
            jwt_secret="test-secret",
            content_ege_db_path=rag_content_dbs["ege"],
            content_oge_db_path=rag_content_dbs["oge"],
            content_lectures_db_path=rag_content_dbs["lectures"],
        )

        yield {
            "session": session,
            "student": student,
            "student_id": student_id,
            "active_session_id": active_session.id,
            "settings": settings,
            "session_maker": session_maker,
        }

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_my_homework_lists_only_active_assignments(
    student_tools_env,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.tutor.student_tools.get_settings",
        lambda: student_tools_env["settings"],
    )
    service = StudentTutorToolsService(
        student_tools_env["session"],
        user=student_tools_env["student"],
    )
    items = await service.get_my_homework()

    assert len(items) == 1
    assert items[0].title == "Активное ДЗ"
    assert items[0].status == HomeworkStatus.ASSIGNED


@pytest.mark.asyncio
async def test_analyze_my_mistakes_aggregates_by_type(
    student_tools_env,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.tutor.student_tools.get_settings",
        lambda: student_tools_env["settings"],
    )
    monkeypatch.setattr(
        "app.services.tutor.tasks.get_settings",
        lambda: student_tools_env["settings"],
    )

    service = StudentTutorToolsService(
        student_tools_env["session"],
        user=student_tools_env["student"],
    )
    analysis = await service.analyze_my_mistakes(limit=20)

    assert analysis.total_incorrect_steps == 2
    assert analysis.by_type
    assert analysis.by_type[0].task_type == 15
    assert analysis.by_type[0].mistake_count == 2
    assert "correct_ans" not in analysis.model_dump_json()


@pytest.mark.asyncio
async def test_analyze_my_mistakes_excludes_active_session(
    student_tools_env,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.tutor.student_tools.get_settings",
        lambda: student_tools_env["settings"],
    )
    monkeypatch.setattr(
        "app.services.tutor.tasks.get_settings",
        lambda: student_tools_env["settings"],
    )

    service = StudentTutorToolsService(
        student_tools_env["session"],
        user=student_tools_env["student"],
    )
    analysis = await service.analyze_my_mistakes(
        limit=20,
        exclude_active_session_id=student_tools_env["active_session_id"],
    )

    assert analysis.total_incorrect_steps == 1


@pytest.mark.asyncio
async def test_list_incorrect_steps_scoped_to_student(student_tools_env) -> None:
    repo = TestSessionRepository(student_tools_env["session"])
    rows = await repo.list_incorrect_steps(student_tools_env["student_id"], limit=10)

    assert len(rows) == 2
    assert all(row.session_id != uuid.UUID(int=0) for row in rows)


@pytest.mark.asyncio
async def test_recommend_topics_from_mistakes(
    student_tools_env,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.tutor.student_tools.get_settings",
        lambda: student_tools_env["settings"],
    )
    monkeypatch.setattr(
        "app.services.tutor.tasks.get_settings",
        lambda: student_tools_env["settings"],
    )

    service = StudentTutorToolsService(
        student_tools_env["session"],
        user=student_tools_env["student"],
    )
    recommendations = await service.recommend_topics(
        exclude_active_session_id=student_tools_env["active_session_id"],
    )

    assert recommendations
    assert recommendations[0].topic in {"Алканы", "Алкены", "Органическая химия"}
    assert recommendations[0].mistake_count >= 1
