"""Unit tests for tutor task tools (offline, fixture SQLite)."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.tutor.context import TutorRunContext
from app.services.tutor.tasks import get_task, question_requires_image, search_tasks
from app.services.tutor.tools import build_tools


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
