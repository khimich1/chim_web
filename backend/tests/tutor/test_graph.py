"""Unit tests for tutor agent graph routing and prompts (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END

from app.services.tutor.context import TutorRunContext
from app.services.tutor.graph import route_after_agent
from app.services.tutor.prompts import build_system_prompt
from app.services.tutor.tools import build_tools


def test_route_to_tools_when_tool_calls_present() -> None:
    ai = AIMessage(
        content="",
        tool_calls=[{"name": "retrieve_theory", "args": {"query": "алканы"}, "id": "1"}],
    )
    state = {"messages": [HumanMessage(content="что такое алканы?"), ai]}
    assert route_after_agent(state) == "tools"


def test_route_to_end_without_tool_calls() -> None:
    ai = AIMessage(content="Алканы — предельные углеводороды.")
    state = {"messages": [HumanMessage(content="привет"), ai]}
    assert route_after_agent(state) == END


def test_build_system_prompt_includes_profile_and_track() -> None:
    ctx = TutorRunContext(track="ege", user_id="u1", role="student")
    prompt = build_system_prompt(ctx, profile={"grade": "11 класс", "exam": "ege"})
    assert "11 класс" in prompt
    assert "EGE" in prompt
    assert "retrieve_theory" in prompt


def test_teacher_prompt_differs_from_student() -> None:
    student = build_system_prompt(TutorRunContext(track="oge", role="student"), {})
    teacher = build_system_prompt(TutorRunContext(track="oge", role="teacher"), {})
    assert "методический" in teacher.lower() or "преподавателя" in teacher.lower()
    assert student != teacher


def test_build_tools_include_task_tools() -> None:
    ctx = TutorRunContext(track="ege", user_id="u1")
    names = {tool.name for tool in build_tools(ctx)}
    assert {"retrieve_theory", "get_task", "search_tasks", "save_user_info"} <= names
    assert "get_my_homework" not in names


def test_build_tools_include_student_tools_when_wired() -> None:
    import asyncio
    from unittest.mock import MagicMock

    ctx = TutorRunContext(
        track="ege",
        user_id="u1",
        role="student",
        run_async=lambda coro: asyncio.run(coro),
        student_tools_service=MagicMock(),
    )
    names = {tool.name for tool in build_tools(ctx)}
    assert {"get_my_homework", "analyze_my_mistakes", "recommend_topics"} <= names
    assert {"generate_practice", "get_selfcheck"} <= names


def test_save_user_info_persists_in_postgres(tmp_path: Path) -> None:
    import asyncio
    import uuid

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.db.base import Base
    from app.models import User, UserRole
    from app.services.tutor.memory import update_profile
    from app.services.tutor.profile_service import TutorProfileService

    async def _run() -> None:
        db_url = f"sqlite+aiosqlite:///{(tmp_path / 'profile_tool.db').as_posix()}"
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        user_id = uuid.uuid4()

        async with session_maker() as db:
            db.add(
                User(
                    id=user_id,
                    email="graph@test.com",
                    password_hash="hash",
                    role=UserRole.STUDENT,
                )
            )
            await db.flush()
            service = TutorProfileService(db, user_id=user_id)
            loop = asyncio.get_running_loop()

            def run_async(coro):  # type: ignore[no-untyped-def]
                future = asyncio.run_coroutine_threadsafe(coro, loop)
                return future.result(timeout=5)

            ctx = TutorRunContext(
                track="ege",
                user_id=str(user_id),
                run_async=run_async,
                profile_service=service,
            )
            from app.services.tutor.context import set_tutor_context

            set_tutor_context(ctx)
            result = await asyncio.to_thread(
                update_profile,
                "grade",
                "11 класс",
                str(user_id),
            )
            assert result["grade"] == "11 класс"
            await db.commit()

        async with session_maker() as db:
            profile = await TutorProfileService(db, user_id=user_id).load()
            assert profile["grade"] == "11 класс"

        await engine.dispose()

    asyncio.run(_run())


def test_get_task_blocked_during_active_test_session() -> None:
    import uuid

    ctx = TutorRunContext(
        track="ege",
        user_id="u1",
        role="student",
        active_test_session_id=uuid.uuid4(),
    )
    tools = build_tools(ctx)
    get_task_tool = next(t for t in tools if t.name == "get_task")
    raw = get_task_tool.invoke({"task_id": 1})
    data = json.loads(raw)
    assert "error" in data
    assert "тест-сессии" in data["error"].lower()


def test_get_task_allowed_for_gated_incorrect_step(
    rag_content_dbs: dict[str, Path],
    monkeypatch,
) -> None:
    import uuid

    from app.core.config import Settings

    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
        jwt_secret="test-secret",
        content_ege_db_path=rag_content_dbs["ege"],
        content_oge_db_path=rag_content_dbs["oge"],
        content_lectures_db_path=rag_content_dbs["lectures"],
    )
    monkeypatch.setattr("app.services.tutor.tasks.get_settings", lambda: settings)

    ctx = TutorRunContext(
        track="ege",
        user_id="u1",
        role="student",
        active_test_session_id=uuid.uuid4(),
        allowed_solve_test_id=1,
    )
    tools = build_tools(ctx)
    get_task_tool = next(t for t in tools if t.name == "get_task")
    raw = get_task_tool.invoke({"task_id": 1})
    data = json.loads(raw)
    assert "error" not in data
    assert data["id"] == 1
    assert "correct_ans" in data
