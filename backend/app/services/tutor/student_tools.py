"""Student-facing tutor tools — homework, mistakes, topic recommendations (Task 43)."""

from __future__ import annotations

import uuid
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import User, UserRole
from app.models.enums import HomeworkStatus, StepStatus
from app.repositories.app.test_session_repo import TestSessionRepository
from app.repositories.content.lectures import LectureContentRepo
from app.schemas.tutor_student_tools import (
    HomeworkToolItem,
    MistakeAnalysis,
    MistakeByType,
    TopicRecommendation,
)
from app.services.homework_service import HomeworkService
from app.services.rag.documents import ExamTrack
from app.services.tutor.tasks import get_task
from app.services.tutor.type_topic_map import resolve_topic_for_type

_ACTIVE_HOMEWORK_STATUSES = frozenset(
    {HomeworkStatus.ASSIGNED, HomeworkStatus.IN_PROGRESS}
)


class StudentTutorToolsService:
    """Read-only student data for tutor agent tools."""

    def __init__(self, session: AsyncSession, *, user: User) -> None:
        self._session = session
        self._user = user
        self._homework = HomeworkService(session)
        self._test_sessions = TestSessionRepository(session)

    async def get_my_homework(self) -> list[HomeworkToolItem]:
        if self._user.role != UserRole.STUDENT:
            return []

        assignments = await self._homework.list_assignments(self._user)
        items: list[HomeworkToolItem] = []
        for assignment in assignments:
            if assignment.status not in _ACTIVE_HOMEWORK_STATUSES:
                continue
            completed = sum(1 for row in assignment.progress if row.completed)
            items.append(
                HomeworkToolItem(
                    id=assignment.id,
                    title=assignment.title,
                    status=assignment.status,
                    due_at=assignment.due_at,
                    items_count=len(assignment.items),
                    completed_items=completed,
                    active_test_session_id=assignment.active_test_session_id,
                )
            )
        return items

    async def analyze_my_mistakes(
        self,
        *,
        limit: int = 20,
        exclude_active_session_id: uuid.UUID | None = None,
    ) -> MistakeAnalysis:
        if self._user.role != UserRole.STUDENT:
            return MistakeAnalysis(total_incorrect_steps=0, by_type=[])

        limit = max(1, min(limit, 100))
        rows = await self._test_sessions.list_incorrect_steps(
            self._user.id,
            limit=limit,
            exclude_session_id=exclude_active_session_id,
        )
        if not rows:
            return MistakeAnalysis(total_incorrect_steps=0, by_type=[])

        available_topics = self._textbook_topics()
        by_type: dict[int, list[tuple[int, ExamTrack]]] = defaultdict(list)
        for row in rows:
            task = get_task(row.test_id, track=row.track.value)
            task_type = task.type if task is not None else 0
            by_type[task_type].append((row.test_id, row.track.value))

        aggregates: list[MistakeByType] = []
        for task_type in sorted(by_type, key=lambda t: (-len(by_type[t]), t)):
            entries = by_type[task_type]
            test_ids = [test_id for test_id, _ in entries]
            track = entries[0][1]
            topic = (
                resolve_topic_for_type(
                    track,
                    task_type,
                    available_topics=available_topics,
                )
                if task_type > 0
                else None
            )
            aggregates.append(
                MistakeByType(
                    task_type=task_type,
                    topic=topic,
                    mistake_count=len(test_ids),
                    recent_test_ids=test_ids[:5],
                )
            )

        return MistakeAnalysis(
            total_incorrect_steps=len(rows),
            by_type=aggregates,
        )

    async def recommend_topics(
        self,
        *,
        limit: int = 5,
        exclude_active_session_id: uuid.UUID | None = None,
    ) -> list[TopicRecommendation]:
        if self._user.role != UserRole.STUDENT:
            return []

        limit = max(1, min(limit, 10))
        analysis = await self.analyze_my_mistakes(
            limit=50,
            exclude_active_session_id=exclude_active_session_id,
        )
        available_topics = self._textbook_topics()
        topic_stats: dict[str, dict[str, object]] = {}

        for item in analysis.by_type:
            if item.topic is None:
                continue
            bucket = topic_stats.setdefault(
                item.topic,
                {"mistake_count": 0, "task_types": set()},
            )
            bucket["mistake_count"] = int(bucket["mistake_count"]) + item.mistake_count
            task_types = bucket["task_types"]
            assert isinstance(task_types, set)
            task_types.add(item.task_type)

        ranked = sorted(
            topic_stats.items(),
            key=lambda pair: (-int(pair[1]["mistake_count"]), pair[0]),
        )

        recommendations: list[TopicRecommendation] = []
        for priority, (topic, stats) in enumerate(ranked[:limit], start=1):
            mistake_count = int(stats["mistake_count"])
            task_types = sorted(stats["task_types"])  # type: ignore[arg-type]
            recommendations.append(
                TopicRecommendation(
                    topic=topic,
                    priority=priority,
                    mistake_count=mistake_count,
                    related_task_types=task_types,
                    reason=(
                        f"По заданиям типа {', '.join(str(t) for t in task_types)} "
                        f"зафиксировано {mistake_count} ошибок."
                    ),
                )
            )

        if not recommendations and available_topics:
            recommendations.append(
                TopicRecommendation(
                    topic=next(iter(sorted(available_topics))),
                    priority=1,
                    mistake_count=0,
                    related_task_types=[],
                    reason="Пока нет накопленных ошибок — повторите базовую тему учебника.",
                )
            )
        return recommendations

    def _textbook_topics(self) -> set[str]:
        settings = get_settings()
        repo = LectureContentRepo(settings.content_lectures_db_path)
        return {topic.topic for topic in repo.list_topics()}
