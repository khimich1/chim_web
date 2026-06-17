"""Unit tests for tutor agent graph routing and prompts (offline)."""

from __future__ import annotations

import json

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


def test_save_user_info_persists(tmp_path, monkeypatch) -> None:
    from app.core.config import Settings

    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
        jwt_secret="test-secret",
        tutor_profile_dir=tmp_path,
    )
    monkeypatch.setattr("app.services.tutor.memory.get_settings", lambda: settings)

    ctx = TutorRunContext(track="ege", user_id="student-1")
    tools = build_tools(ctx)
    save_tool = next(t for t in tools if t.name == "save_user_info")
    raw = save_tool.invoke({"key": "grade", "value": "11 класс"})
    data = json.loads(raw)

    assert data["status"] == "saved"
    profile_file = tmp_path / "student-1.json"
    assert profile_file.is_file()
    saved = json.loads(profile_file.read_text(encoding="utf-8"))
    assert saved["grade"] == "11 класс"


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
