"""Deterministic context assembly for solve-pipeline (§17.2)."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from app.services.rag.theory import TheoryHit, search_theory
from app.services.tutor.context import TutorRunContext, get_tutor_context
from app.services.tutor.solve.state import SolveState
from app.services.tutor.solve.task_flow import build_theory_query, extract_task_id
from app.services.tutor.tasks import get_task, question_requires_image
from app.services.tutor.validation import detect_answer_format

logger = logging.getLogger(__name__)


def _last_user_text(state: SolveState) -> str:
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            content = message.content
            return content if isinstance(content, str) else str(content)
    return ""


def _hits_to_payload(hits: list[TheoryHit]) -> list[dict[str, Any]]:
    return [
        {
            "content": hit.content,
            "topic": hit.topic,
            "chunk_title": hit.chunk_title,
            "chunk_idx": hit.chunk_idx,
            "source": hit.source,
        }
        for hit in hits
    ]


def make_prepare_context_node(ctx: TutorRunContext | None = None):
    """Build graph node: get_task + retrieve_theory in code (not via LLM tools)."""

    def prepare_context(state: SolveState) -> dict[str, Any]:
        run_ctx = ctx or get_tutor_context()
        user_text = _last_user_text(state)

        if (
            run_ctx.role == "student"
            and run_ctx.active_test_session_id is not None
            and run_ctx.allowed_solve_test_id is None
        ):
            return {
                "messages": [
                    AIMessage(
                        content=(
                            "Разбор заданий с ключом недоступен во время активной "
                            "тест-сессии. Сначала проверьте ответ на шаге — после "
                            "ошибки станет доступна кнопка «Спросить советчика»."
                        )
                    )
                ],
            }

        task_id = extract_task_id(user_text)
        if run_ctx.allowed_solve_test_id is not None:
            if task_id is not None and task_id != run_ctx.allowed_solve_test_id:
                return {
                    "messages": [
                        AIMessage(
                            content=(
                                "Разбор с ключом доступен только для текущего "
                                "неверного шага теста."
                            )
                        )
                    ],
                }
            task_id = run_ctx.allowed_solve_test_id
        elif task_id is None:
            return {
                "messages": [
                    AIMessage(
                        content=(
                            "Не удалось определить номер задания. "
                            "Напишите, например: «разбери задание 5»."
                        )
                    )
                ],
            }

        logger.info("solve_pipeline get_task(%s)", task_id)
        task = get_task(task_id, track=run_ctx.track)
        if task is None:
            return {
                "messages": [
                    AIMessage(
                        content=(
                            f"Задание {task_id} не найдено в банке {run_ctx.track.upper()} "
                            "или помечено как бракованное."
                        )
                    )
                ],
            }

        theory_query = build_theory_query(task.question)
        hits = search_theory(theory_query, track=run_ctx.track, top_k=4)
        theory_hits = _hits_to_payload(hits)

        task_context = {
            "id": task.id,
            "type": task.type,
            "question": task.question,
            "requires_image": question_requires_image(task.question),
        }
        answer_format = detect_answer_format(task.type, task.correct_ans)

        payload: dict[str, Any] = {
            "task_id": task_id,
            "task_context": task_context,
            "correct_ans": task.correct_ans,
            "theory_hits": theory_hits,
            "answer_format": answer_format,
            "retry_count": 0,
            "fix_instructions": "",
        }
        if run_ctx.solve_student_answer is not None:
            payload["student_answer"] = run_ctx.solve_student_answer
        return payload

    return prepare_context


def route_after_prepare_context(state: SolveState) -> str:
    """Skip solver when prepare_context already emitted a terminal AIMessage."""
    last = state["messages"][-1]
    if isinstance(last, AIMessage):
        return "end"
    if state.get("task_context") is None:
        return "end"
    return "solver"
