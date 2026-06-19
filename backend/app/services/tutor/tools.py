"""LangGraph tool definitions for the chemistry tutor agent."""

from __future__ import annotations

import json

from langchain_core.tools import BaseTool, tool

from app.services.rag.theory import search_theory
from app.services.tutor.context import TutorRunContext
from app.services.tutor.memory import update_profile
from app.services.tutor.tasks import (
    get_task as repo_get_task,
    question_requires_image,
    search_tasks as repo_search_tasks,
)

ALLOWED_PROFILE_KEYS: frozenset[str] = frozenset(
    {"name", "grade", "exam", "weak_topics", "goal"}
)


def build_tools(ctx: TutorRunContext) -> list[BaseTool]:
    """Build tool set bound to the current user/track context."""

    @tool
    def retrieve_theory(query: str, top_k: int = 5) -> str:
        """Поиск теории по учебнику химии.

        Используй для вопросов «что такое…», объяснений понятий и теоретической
        базы при разборе задачи. Возвращает JSON с content, topic, chunk_title.
        """
        hits = search_theory(query, track=ctx.track, top_k=top_k)
        payload = [
            {
                "content": hit.content,
                "topic": hit.topic,
                "chunk_title": hit.chunk_title,
                "chunk_idx": hit.chunk_idx,
                "source": hit.source,
            }
            for hit in hits
        ]
        return json.dumps(payload, ensure_ascii=False)

    @tool
    def save_user_info(key: str, value: str) -> str:
        """Сохранить факт о пользователе (name, grade, exam, weak_topics, goal)."""
        normalized_key = key.strip().lower()
        if normalized_key not in ALLOWED_PROFILE_KEYS:
            allowed = ", ".join(sorted(ALLOWED_PROFILE_KEYS))
            return json.dumps(
                {"error": f"Недопустимый ключ {key!r}. Разрешены: {allowed}"},
                ensure_ascii=False,
            )
        clean_value = value.strip()
        if not clean_value:
            return json.dumps(
                {"error": "Пустое значение не сохраняется"},
                ensure_ascii=False,
            )
        update_profile(normalized_key, clean_value, ctx.user_id)
        return json.dumps(
            {"status": "saved", "key": normalized_key, "value": clean_value},
            ensure_ascii=False,
        )

    @tool
    def get_task(task_id: int) -> str:
        """Получить задание по id из банка задач текущего трека (ЕГЭ/ОГЭ)."""
        if ctx.active_test_session_id is not None and ctx.role == "student":
            if ctx.allowed_solve_test_id != task_id:
                return json.dumps(
                    {
                        "error": (
                            "Разбор заданий с ключом недоступен во время активной "
                            "тест-сессии. Задайте вопрос по теории."
                        )
                    },
                    ensure_ascii=False,
                )

        task = repo_get_task(task_id, track=ctx.track)
        if task is None:
            return json.dumps(
                {"error": f"Задание {task_id} не найдено или помечено как бракованное"},
                ensure_ascii=False,
            )
        return json.dumps(
            {
                "id": task.id,
                "question": task.question,
                "correct_ans": task.correct_ans,
                "type": task.type,
                "requires_image": question_requires_image(task.question),
            },
            ensure_ascii=False,
        )

    @tool
    def search_tasks(
        query: str | None = None,
        task_type: int | None = None,
        top_k: int = 5,
    ) -> str:
        """Найти задания в банке по подстроке в тексте и/или номеру задания (type)."""
        results = repo_search_tasks(
            track=ctx.track,
            query=query,
            task_type=task_type,
            top_k=top_k,
        )
        payload = [
            {
                "id": item.id,
                "type": item.type,
                "question_preview": item.question_preview,
            }
            for item in results
        ]
        return json.dumps(payload, ensure_ascii=False)

    tools: list[BaseTool] = [retrieve_theory, save_user_info, get_task, search_tasks]

    if ctx.role == "student" and ctx.student_tools_service is not None and ctx.run_async is not None:
        service = ctx.student_tools_service
        run = ctx.run_async

        @tool
        def get_my_homework() -> str:
            """Список активных домашних заданий ученика со статусом и сроком."""
            items = run(service.get_my_homework())
            payload = [item.model_dump(mode="json") for item in items]
            return json.dumps(payload, ensure_ascii=False)

        @tool
        def analyze_my_mistakes(limit: int = 20) -> str:
            """Анализ последних ошибок в тестах: агрегация по типу задания (type)."""
            analysis = run(
                service.analyze_my_mistakes(
                    limit=limit,
                    exclude_active_session_id=ctx.active_test_session_id,
                )
            )
            return json.dumps(analysis.model_dump(mode="json"), ensure_ascii=False)

        @tool
        def recommend_topics() -> str:
            """Рекомендации тем учебника для повторения на основе слабых мест."""
            topics = run(
                service.recommend_topics(
                    exclude_active_session_id=ctx.active_test_session_id,
                )
            )
            payload = [item.model_dump(mode="json") for item in topics]
            return json.dumps(payload, ensure_ascii=False)

        @tool
        def generate_practice(
            topic: str | None = None,
            task_type: int | None = None,
            n: int = 5,
        ) -> str:
            """Подобрать задания для тренировки (id и текст вопроса, без ответов)."""
            if ctx.active_test_session_id is not None:
                return json.dumps(
                    {
                        "error": (
                            "Подбор заданий для тренировки недоступен во время "
                            "активной тест-сессии. Задайте вопрос по теории."
                        )
                    },
                    ensure_ascii=False,
                )
            items = run(
                service.generate_practice(topic=topic, task_type=task_type, n=n)
            )
            payload = [item.model_dump(mode="json") for item in items]
            return json.dumps(payload, ensure_ascii=False)

        @tool
        def get_selfcheck(topic: str) -> str:
            """Вопросы самопроверки из учебника по теме (Q/A из lecture_qa)."""
            items = run(service.get_selfcheck(topic))
            payload = [item.model_dump(mode="json") for item in items]
            return json.dumps(payload, ensure_ascii=False)

        tools.extend(
            [
                get_my_homework,
                analyze_my_mistakes,
                recommend_topics,
                generate_practice,
                get_selfcheck,
            ]
        )

    return tools
