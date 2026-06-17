"""Unit tests for solve-pipeline routing, gating, and critic (mock LLM)."""

from __future__ import annotations

import uuid
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage

from app.services.rag.theory import TheoryHit
from app.services.tutor.context import TutorRunContext
from app.services.tutor.graph import build_graph, route_after_input_guard
from app.services.tutor.solve.critic import MAX_CRITIC_RETRIES, run_code_critic
from app.services.tutor.solve.intent_router import route_intent, should_use_solve_pipeline
from app.services.tutor.solve.prepare_context import make_prepare_context_node
from app.services.tutor.solve.task_flow import extract_task_id


def _mock_theory_hits(*_args, **_kwargs) -> list[TheoryHit]:
    return [
        TheoryHit(
            content="Алканы малореакционны.",
            topic="Алканы",
            chunk_title="Свойства алканов",
            chunk_idx=0,
            source="lecture",
        )
    ]


class SequenceLLM:
    """Returns canned solver drafts in order."""

    def __init__(self, drafts: list[str]) -> None:
        self._drafts = list(drafts)
        self.calls = 0

    def bind_tools(self, tools, parallel_tool_calls=False):  # noqa: ANN001
        return self

    def invoke(self, messages):  # noqa: ANN001
        system_text = str(getattr(messages[0], "content", "")) if messages else ""
        if "классификатор" in system_text.lower():
            return AIMessage(content="да")
        draft = self._drafts[min(self.calls, len(self._drafts) - 1)]
        self.calls += 1
        return AIMessage(content=draft)


def test_extract_task_id_from_ru_phrases() -> None:
    assert extract_task_id("разбери задание 5") == 5
    assert extract_task_id("помоги с задачей №12") == 12
    assert extract_task_id("что такое алканы") is None


def test_should_use_solve_pipeline_gating_during_active_test() -> None:
    active = TutorRunContext(
        track="ege",
        user_id="u1",
        role="student",
        active_test_session_id=uuid.uuid4(),
    )
    assert not should_use_solve_pipeline("разбери задание 1", active)
    assert route_intent(
        {"messages": [HumanMessage(content="разбери задание 1")]},
        active,
    ) == "general_agent"


def test_route_after_input_guard_sends_solve_intent_to_prepare_context() -> None:
    ctx = TutorRunContext(track="ege", user_id="u1", role="student")
    state = {"messages": [HumanMessage(content="разбери задание 3")]}
    assert route_after_input_guard(state, ctx) == "prepare_context"


def test_prepare_context_calls_get_task_and_retrieve_theory(
    rag_content_dbs: dict[str, Path],
    rag_retriever,
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
    monkeypatch.setattr(
        "app.services.tutor.solve.prepare_context.search_theory",
        _mock_theory_hits,
    )

    ctx = TutorRunContext(track="ege", user_id="u1")
    node = make_prepare_context_node(ctx)
    result = node(
        {
            "messages": [HumanMessage(content="разбери задание 1")],
        }
    )

    assert result["task_id"] == 1
    assert result["task_context"]["id"] == 1
    assert result["correct_ans"] == "secret-answer"
    assert result["theory_hits"]
    assert result["theory_hits"][0]["topic"] == "Алканы"


def test_run_code_critic_rejects_wrong_key() -> None:
    critique = run_code_critic(
        {
            "draft_answer": "Теория...\nОтвет: 99",
            "correct_ans": "12",
            "answer_format": "digit_string",
            "theory_hits": [{"topic": "Алканы", "chunk_title": "Свойства"}],
            "task_context": {"question": "Условие из БД", "type": 15},
        }
    )
    assert not critique.approved
    assert any("ключ" in issue for issue in critique.issues)


def test_solve_graph_end_to_end_with_mock_llm(
    rag_content_dbs: dict[str, Path],
    rag_retriever,
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
    monkeypatch.setattr(
        "app.services.tutor.solve.prepare_context.search_theory",
        _mock_theory_hits,
    )

    good_draft = (
        "EGE question\n"
        "По теме «Алканы — Свойства алканов» алканы малореакционны.\n"
        "Ответ: secret-answer"
    )
    llm = SequenceLLM([good_draft])
    ctx = TutorRunContext(track="ege", user_id="u1", role="student")
    graph = build_graph(ctx, llm=llm, settings=settings)
    result = graph.invoke(
        {"messages": [HumanMessage(content="разбери задание 1")]}
    )

    assert "secret-answer" in result["messages"][-1].content
    assert result.get("theory_hits")
    assert llm.calls >= 1


def test_solve_graph_retries_then_finalizes_on_persistent_critic_failure(
    rag_content_dbs: dict[str, Path],
    rag_retriever,
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
    monkeypatch.setattr(
        "app.services.tutor.solve.prepare_context.search_theory",
        _mock_theory_hits,
    )

    bad_draft = "Короткий ответ без цитаты.\nОтвет: wrong"
    llm = SequenceLLM([bad_draft, bad_draft, bad_draft])
    ctx = TutorRunContext(track="ege", user_id="u1", role="student")
    graph = build_graph(ctx, llm=llm, settings=settings)
    result = graph.invoke(
        {"messages": [HumanMessage(content="разбери задачу 1")]}
    )

    assert "Эталонный ответ" in result["messages"][-1].content
    assert llm.calls >= MAX_CRITIC_RETRIES
