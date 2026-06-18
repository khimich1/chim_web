"""Unit tests for tutor task tools (offline, fixture SQLite)."""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.base import Base
from app.models import StudentProfile, User, UserRole
from app.models.enums import ExamTrack
from app.services.tutor.context import TutorRunContext
from app.services.tutor.student_tools import StudentTutorToolsService
from app.services.tutor.tasks import get_task, question_requires_image, search_tasks
from app.services.tutor.tools import build_tools
from app.services.tutor.type_topic_map import task_types_for_topic


def test_question_requires_image_detects_markers() -> None:
    assert question_requires_image("См. рисунок 1")
    assert not question_requires_image("Рассчитайте массу вещества")


def test_get_task_from_fixture_db(rag_content_dbs: dict[str, Path], monkeypatch) -> None:
    from app.core.config import Settings

    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
        jwt_secret="test-secret",
        content_ege_db_path=rag_content_dbs["ege"],
        content_oge_db_path=rag_content_dbs["oge"],
        content_lectures_db_path=rag_content_dbs["lectures"],
    )
    monkeypatch.setattr("app.services.tutor.tasks.get_settings", lambda: settings)

    task = get_task(1, track="ege")
    assert task is not None
    assert task.type == 15
    assert "secret-answer" in task.correct_ans


def test_search_tasks_respects_track(rag_content_dbs: dict[str, Path], monkeypatch) -> None:
    from app.core.config import Settings

    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
        jwt_secret="test-secret",
        content_ege_db_path=rag_content_dbs["ege"],
        content_oge_db_path=rag_content_dbs["oge"],
        content_lectures_db_path=rag_content_dbs["lectures"],
    )
    monkeypatch.setattr("app.services.tutor.tasks.get_settings", lambda: settings)

    ege_results = search_tasks(track="ege", query="EGE")
    oge_results = search_tasks(track="oge", query="OGE")
    assert ege_results
    assert oge_results
    assert "EGE" in ege_results[0].question_preview
    assert "OGE" in oge_results[0].question_preview


def test_retrieve_theory_tool_returns_json(
    rag_retriever,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.rag.theory.Retriever.from_settings",
        lambda settings=None: rag_retriever,
    )

    ctx = TutorRunContext(track="ege", user_id="u1")
    tools = build_tools(ctx)
    theory_tool = next(t for t in tools if t.name == "retrieve_theory")
    raw = theory_tool.invoke({"query": "алканы малореакционны", "top_k": 3})
    hits = json.loads(raw)

    assert isinstance(hits, list)
    assert hits
    assert hits[0]["topic"] == "Алканы"


def test_task_types_for_topic_reverse_mapping() -> None:
    types = task_types_for_topic(
        "ege",
        "Алканы",
        available_topics={"Алканы", "Соли"},
    )
    assert 15 in types


def test_generate_practice_tool_omits_correct_ans(
    rag_content_dbs: dict[str, Path],
    monkeypatch,
) -> None:
    from app.core.config import Settings

    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
        jwt_secret="test-secret",
        content_ege_db_path=rag_content_dbs["ege"],
        content_oge_db_path=rag_content_dbs["oge"],
        content_lectures_db_path=rag_content_dbs["lectures"],
    )
    monkeypatch.setattr("app.services.tutor.tasks.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.tutor.student_tools.get_settings", lambda: settings)

    service = MagicMock()
    service.generate_practice = AsyncMock(
        return_value=[
            MagicMock(
                model_dump=lambda mode="json": {
                    "id": 1,
                    "type": 15,
                    "question": "EGE question",
                }
            )
        ]
    )

    ctx = TutorRunContext(
        track="ege",
        user_id="u1",
        role="student",
        run_async=lambda coro: asyncio.run(coro),
        student_tools_service=service,
    )
    tool = next(t for t in build_tools(ctx) if t.name == "generate_practice")
    payload = json.loads(tool.invoke({"task_type": 15, "n": 3}))

    assert len(payload) == 1
    assert payload[0]["question"] == "EGE question"
    assert "correct_ans" not in payload[0]
    service.generate_practice.assert_awaited_once_with(
        topic=None,
        task_type=15,
        n=3,
    )


def test_generate_practice_blocked_during_active_test_session() -> None:
    service = MagicMock()
    ctx = TutorRunContext(
        track="ege",
        user_id="u1",
        role="student",
        active_test_session_id=uuid.uuid4(),
        run_async=lambda coro: asyncio.run(coro),
        student_tools_service=service,
    )
    tool = next(t for t in build_tools(ctx) if t.name == "generate_practice")
    payload = json.loads(tool.invoke({"task_type": 15}))

    assert "error" in payload
    service.generate_practice.assert_not_called()


def test_get_selfcheck_tool_returns_qa_pairs(
    rag_content_dbs: dict[str, Path],
    monkeypatch,
) -> None:
    from app.core.config import Settings

    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
        jwt_secret="test-secret",
        content_ege_db_path=rag_content_dbs["ege"],
        content_oge_db_path=rag_content_dbs["oge"],
        content_lectures_db_path=rag_content_dbs["lectures"],
    )
    monkeypatch.setattr("app.services.tutor.student_tools.get_settings", lambda: settings)

    service = MagicMock()
    service.get_selfcheck = AsyncMock(
        return_value=[
            MagicMock(
                model_dump=lambda mode="json": {
                    "question": "Почему алканы малореакционны?",
                    "answer": "Из-за неполярных связей.",
                    "chunk_idx": 0,
                    "chunk_title": "Свойства алканов",
                }
            )
        ]
    )

    ctx = TutorRunContext(
        track="ege",
        user_id="u1",
        role="student",
        run_async=lambda coro: asyncio.run(coro),
        student_tools_service=service,
    )
    tool = next(t for t in build_tools(ctx) if t.name == "get_selfcheck")
    payload = json.loads(tool.invoke({"topic": "Алканы"}))

    assert len(payload) == 1
    assert payload[0]["question"].startswith("Почему алканы")
    service.get_selfcheck.assert_awaited_once_with("Алканы")


@pytest.fixture
async def practice_tools_env(tmp_path: Path, rag_content_dbs: dict[str, Path], monkeypatch):
    from app.core.config import Settings

    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
        jwt_secret="test-secret",
        content_ege_db_path=rag_content_dbs["ege"],
        content_oge_db_path=rag_content_dbs["oge"],
        content_lectures_db_path=rag_content_dbs["lectures"],
    )
    monkeypatch.setattr("app.services.tutor.tasks.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.tutor.student_tools.get_settings", lambda: settings)

    db_file = tmp_path / "practice_tools.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
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
        session.add_all([teacher, student])
        session.add(
            StudentProfile(
                user_id=student_id,
                teacher_id=teacher_id,
                track=ExamTrack.EGE,
            )
        )
        await session.commit()

    yield {
        "session_factory": session_factory,
        "student_id": student_id,
        "settings": settings,
    }

    await engine.dispose()


@pytest.mark.asyncio
async def test_generate_practice_service_filters_by_track_and_type(
    practice_tools_env,
) -> None:
    async with practice_tools_env["session_factory"]() as session:
        student = await session.get(User, practice_tools_env["student_id"])
        assert student is not None
        service = StudentTutorToolsService(session, user=student)
        items = await service.generate_practice(task_type=15, n=5)

    assert items
    assert all(item.type == 15 for item in items)
    assert all("secret-answer" not in item.question for item in items)
    assert all(not hasattr(item, "correct_ans") for item in items)


@pytest.mark.asyncio
async def test_get_selfcheck_service_returns_textbook_qa(practice_tools_env) -> None:
    async with practice_tools_env["session_factory"]() as session:
        student = await session.get(User, practice_tools_env["student_id"])
        assert student is not None
        service = StudentTutorToolsService(session, user=student)
        items = await service.get_selfcheck("Алканы")

    assert len(items) == 1
    assert "малореакционны" in items[0].question.lower()
    assert items[0].chunk_title == "Свойства алканов"

