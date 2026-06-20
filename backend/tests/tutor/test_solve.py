"""Unit tests for solve-pipeline routing, gating, and critic (mock LLM)."""

from __future__ import annotations

import uuid
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage

from app.services.rag.theory import TheoryHit
from app.services.tutor.context import TutorRunContext
from app.services.tutor.graph import build_graph, route_after_input_guard
from app.services.tutor.solve.critic import MAX_CRITIC_RETRIES, run_code_critic, run_critic, run_llm_chemical_critic
from app.services.tutor.solve.intent_router import route_intent, should_use_solve_pipeline
from app.services.tutor.solve.planner import needs_planner
from app.services.tutor.solve.prepare_context import make_prepare_context_node, route_after_prepare_context
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


def test_should_use_solve_pipeline_allows_explain_incorrect_step() -> None:
    active = TutorRunContext(
        track="ege",
        user_id="u1",
        role="student",
        active_test_session_id=uuid.uuid4(),
        allowed_solve_test_id=42,
        solve_student_answer="99",
    )
    assert should_use_solve_pipeline("разбери задание 42", active)
    assert not should_use_solve_pipeline("разбери задание 99", active)
    assert should_use_solve_pipeline(
        "Объясни, в чём ошибка, и сравни с правильным ответом.",
        active,
    )
    assert route_intent(
        {
            "messages": [
                HumanMessage(
                    content="Разбери задание 42. Мой ответ: «99». Объясни ошибку."
                )
            ]
        },
        active,
    ) == "solve_pipeline"


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


def test_prepare_context_uses_allowed_test_id_during_active_session(
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

    ctx = TutorRunContext(
        track="ege",
        user_id="u1",
        role="student",
        active_test_session_id=uuid.uuid4(),
        allowed_solve_test_id=1,
        solve_student_answer="wrong",
    )
    node = make_prepare_context_node(ctx)
    result = node(
        {
            "messages": [
                HumanMessage(
                    content="Объясни, в чём ошибка, и сравни с правильным ответом."
                )
            ],
        }
    )

    assert result["task_id"] == 1
    assert result["student_answer"] == "wrong"
    assert result["correct_ans"] == "secret-answer"


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


def test_needs_planner_for_complex_task_types() -> None:
    assert needs_planner(7)
    assert needs_planner(8)
    assert needs_planner(26)
    assert needs_planner(15) is False


def test_route_after_prepare_context_sends_complex_types_to_planner() -> None:
    simple = {
        "messages": [HumanMessage(content="разбери задание 1")],
        "task_context": {"id": 1, "type": 15, "question": "q"},
    }
    complex_state = {
        "messages": [HumanMessage(content="разбери задание 1")],
        "task_context": {"id": 1, "type": 7, "question": "q"},
    }
    assert route_after_prepare_context(simple) == "solver"
    assert route_after_prepare_context(complex_state) == "planner"


def test_run_llm_chemical_critic_rejects_inconsistent_draft(monkeypatch) -> None:
    from app.services.tutor.solve import critic as critic_module

    def _fake_invoke(*_args, **_kwargs):
        from app.services.tutor.solve.critic import _ChemicalCritiqueOutput

        return _ChemicalCritiqueOutput(
            approved=False,
            issues=["неверная формула продукта"],
            fix_instructions="Пересчитай продукты реакции",
        )

    monkeypatch.setattr(critic_module, "_invoke_chemical_critic_llm", _fake_invoke)

    critique = run_llm_chemical_critic(
        {
            "draft_answer": "А → 1\nОтвет: 12",
            "task_context": {"type": 7, "question": "Установите соответствие"},
        },
        llm=SequenceLLM(["ignored"]),
        ctx=TutorRunContext(track="ege", user_id="u1"),
    )
    assert not critique.approved
    assert "формула" in critique.issues[0]


def test_run_critic_runs_llm_only_for_complex_types(monkeypatch) -> None:
    from app.services.tutor.solve import critic as critic_module

    calls: list[str] = []

    def _fake_chemical(*_args, **_kwargs):
        calls.append("llm")
        from app.services.tutor.solve.critic import Critique

        return Critique(approved=True)

    monkeypatch.setattr(critic_module, "run_llm_chemical_critic", _fake_chemical)

    good_state = {
        "draft_answer": (
            "EGE question\n"
            "По теме «Алканы — Свойства алканов» алканы малореакционны.\n"
            "Ответ: secret-answer"
        ),
        "correct_ans": "secret-answer",
        "answer_format": "digit_string",
        "theory_hits": [{"topic": "Алканы", "chunk_title": "Свойства алканов"}],
        "task_context": {"question": "EGE question", "type": 15},
    }
    run_critic(good_state, llm=SequenceLLM(["x"]))
    assert calls == []

    complex_state = {**good_state, "task_context": {"question": "EGE question", "type": 7}}
    run_critic(complex_state, llm=SequenceLLM(["x"]))
    assert calls == ["llm"]


def test_solve_graph_uses_planner_for_complex_type(
    rag_content_dbs: dict[str, Path],
    rag_retriever,
    monkeypatch,
) -> None:
    from app.core.config import Settings
    from app.repositories.content.tests import TestQuestion
    from app.services.tutor.solve import planner as planner_module
    import app.services.tutor.graph as graph_module

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
    complex_task = TestQuestion(
        id=7,
        filename="007.txt",
        type=7,
        question="Установите соответствие между веществами и свойствами",
        options=None,
        correct_ans="secret-answer",
        hint=None,
        detailed_explanation=None,
    )
    monkeypatch.setattr(
        "app.services.tutor.solve.prepare_context.get_task",
        lambda task_id, track="ege": complex_task,
    )

    planner_calls: list[str] = []
    original_planner = planner_module.make_planner_node

    def _tracking_planner(llm, ctx=None):
        node = original_planner(llm, ctx)

        def wrapped(state):
            planner_calls.append("planner")
            return node(state)

        return wrapped

    monkeypatch.setattr(graph_module, "make_planner_node", _tracking_planner)

    good_draft = (
        "Установите соответствие между веществами и свойствами\n"
        "А → secret\n"
        "По теме «Алканы — Свойства алканов» алканы малореакционны.\n"
        "Ответ: secret-answer"
    )
    llm = SequenceLLM([good_draft])
    ctx = TutorRunContext(track="ege", user_id="u1", role="student")
    graph = build_graph(ctx, llm=llm, settings=settings)
    result = graph.invoke(
        {"messages": [HumanMessage(content="разбери задание 7")]}
    )

    assert planner_calls == ["planner"]
    assert "secret-answer" in result["messages"][-1].content
