"""LLM solver node for deterministic solve-pipeline."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.services.tutor.context import TutorRunContext, get_tutor_context
from app.services.tutor.solve.state import SolveState


def _format_theory_block(theory_hits: list[dict[str, Any]]) -> str:
    if not theory_hits:
        return "Фрагменты учебника не найдены."
    parts: list[str] = []
    for hit in theory_hits:
        topic = hit.get("topic") or "?"
        chunk_title = hit.get("chunk_title") or "?"
        content = hit.get("content") or ""
        parts.append(f"### {topic} — {chunk_title}\n{content}")
    return "\n\n".join(parts)


def _build_solver_messages(state: SolveState) -> list[SystemMessage | HumanMessage]:
    task_context = state.get("task_context") or {}
    theory_hits = state.get("theory_hits") or []
    correct_ans = state.get("correct_ans") or ""
    answer_format = state.get("answer_format") or "digit_string"
    fix_instructions = (state.get("fix_instructions") or "").strip()

    requires_image = bool(task_context.get("requires_image"))
    image_note = (
        "В задании есть рисунок/схема — предупреди, что без изображения разбор может быть неполным.\n"
        if requires_image
        else ""
    )
    format_note = (
        "Итоговый ключ — число (можно с единицами измерения в тексте, ключ — число)."
        if answer_format == "number"
        else "Итоговый ключ — последовательность цифр 1–4 в порядке АБВГ (без перестановки)."
    )

    system = SystemMessage(
        content=(
            "Ты — наставник по химии. Построй пошаговый разбор задания для школьника.\n"
            "Правила:\n"
            "1. Используй ТОЛЬКО условие из блока «Задание» и теорию из блока «Учебник».\n"
            "2. Обязательно процитируй тему и раздел учебника (topic / chunk_title).\n"
            "3. Итоговый ответ в конце в формате «Ответ: …» и он ДОЛЖЕН совпадать с эталоном.\n"
            f"4. {format_note}\n"
            f"{image_note}"
            f"5. Эталонный ключ (используй дословно в «Ответ: …»): {correct_ans}\n"
        )
    )
    student_answer = (state.get("student_answer") or "").strip()
    student_block = (
        f"\n## Ответ ученика\n{student_answer}\n"
        "Сравни ответ ученика с эталоном и объясни, в чём ошибка.\n"
        if student_answer
        else ""
    )
    user = HumanMessage(
        content=(
            f"## Задание (id={task_context.get('id')}, type={task_context.get('type')})\n"
            f"{task_context.get('question', '')}\n\n"
            f"## Учебник\n{_format_theory_block(theory_hits)}\n"
            f"{student_block}"
        )
        + (f"\n## Исправления после проверки\n{fix_instructions}\n" if fix_instructions else "")
    )
    return [system, user]


def make_solver_node(llm: ChatOpenAI, ctx: TutorRunContext | None = None):
    def solver(state: SolveState) -> dict[str, Any]:
        _ = ctx or get_tutor_context()
        response = llm.invoke(_build_solver_messages(state))
        content = response.content if isinstance(response.content, str) else str(response.content)
        return {"draft_answer": content.strip()}

    return solver
