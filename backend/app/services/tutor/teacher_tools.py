"""Teacher-facing tutor tools — student analytics and homework drafts (Task 45)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    HomeworkAssignment,
    HomeworkStatus,
    TestSession,
    TestSessionStatus,
    TutorSession,
    User,
    UserRole,
)
from app.repositories.app.student_repo import StudentRepository
from app.repositories.app.test_session_repo import TestSessionRepository
from app.schemas.homework import LectureItem, TestByTypeItem
from app.schemas.tutor_teacher_tools import (
    ClassMistakeAggregate,
    ClassOverview,
    HomeworkDraftPreview,
    StudentActivitySummary,
    StudentSummary,
)
from app.services.tutor.student_tools import StudentTutorToolsService
from app.services.tutor.tasks import get_task
from app.services.tutor.type_topic_map import resolve_topic_for_type


class TeacherTutorToolsService:
    """Read-only teacher analytics for tutor agent tools."""

    def __init__(self, session: AsyncSession, *, user: User) -> None:
        self._session = session
        self._user = user
        self._students = StudentRepository(session)
        self._test_sessions = TestSessionRepository(session)

    async def summarize_student(self, student_id: uuid.UUID) -> StudentSummary | None:
        if self._user.role != UserRole.TEACHER:
            return None

        student = await self._students.get_student_for_teacher(
            student_id,
            self._user.id,
        )
        if student is None or student.student_profile is None:
            return None

        student_service = StudentTutorToolsService(self._session, user=student)
        analysis = await student_service.analyze_my_mistakes(limit=50)
        recommendations = await student_service.recommend_topics(limit=5)
        weak_topics = [item.topic for item in recommendations if item.mistake_count > 0]

        activity = await self._student_activity(student_id)

        return StudentSummary(
            student_id=student.id,
            email=student.email,
            track=student.student_profile.track,
            weak_topics=weak_topics,
            mistakes_by_type=analysis.by_type,
            total_incorrect_steps=analysis.total_incorrect_steps,
            activity=activity,
        )

    async def suggest_homework(self, student_id: uuid.UUID) -> HomeworkDraftPreview | None:
        if self._user.role != UserRole.TEACHER:
            return None

        student = await self._students.get_student_for_teacher(
            student_id,
            self._user.id,
        )
        if student is None:
            return None

        summary = await self.summarize_student(student_id)
        if summary is None:
            return None

        items: list[LectureItem | TestByTypeItem] = []
        for topic in summary.weak_topics[:2]:
            items.append(LectureItem(topic=topic))

        for mistake in summary.mistakes_by_type[:2]:
            if mistake.task_type > 0:
                items.append(TestByTypeItem(types=[mistake.task_type]))

        if not items and summary.weak_topics:
            items.append(LectureItem(topic=summary.weak_topics[0]))

        title = "Повторение слабых тем"
        if summary.weak_topics:
            title = f"Повторение: {', '.join(summary.weak_topics[:2])}"

        description = (
            "Черновик на основе ошибок ученика в тестах. "
            "Проверьте пункты перед назначением."
        )

        return HomeworkDraftPreview(
            student_id=student_id,
            title=title,
            description=description,
            items=items[:5],
        )

    async def class_overview(self) -> ClassOverview:
        if self._user.role != UserRole.TEACHER:
            return ClassOverview(
                total_students=0,
                total_incorrect_steps=0,
                by_type=[],
            )

        students = await self._students.list_by_teacher(self._user.id)
        student_ids = [student.id for student in students]
        if not student_ids:
            return ClassOverview(
                total_students=0,
                total_incorrect_steps=0,
                by_type=[],
            )

        rows = await self._test_sessions.list_incorrect_steps_for_students(
            student_ids,
            limit=500,
        )
        if not rows:
            return ClassOverview(
                total_students=len(student_ids),
                total_incorrect_steps=0,
                by_type=[],
            )

        available_topics = StudentTutorToolsService(
            self._session,
            user=students[0],
        )._textbook_topics()

        by_type: dict[int, dict[str, object]] = {}
        for row in rows:
            task = get_task(row.test_id, track=row.track.value)
            task_type = task.type if task is not None else 0
            bucket = by_type.setdefault(
                task_type,
                {"mistake_count": 0, "student_ids": set(), "track": row.track},
            )
            bucket["mistake_count"] = int(bucket["mistake_count"]) + 1
            student_ids_set = bucket["student_ids"]
            assert isinstance(student_ids_set, set)
            student_ids_set.add(row.student_id)

        aggregates: list[ClassMistakeAggregate] = []
        for task_type in sorted(
            by_type,
            key=lambda t: (-int(by_type[t]["mistake_count"]), t),
        ):
            stats = by_type[task_type]
            mistake_count = int(stats["mistake_count"])
            affected = stats["student_ids"]
            track = stats["track"]
            assert isinstance(affected, set)
            assert hasattr(track, "value")
            topic = (
                resolve_topic_for_type(
                    track.value,
                    task_type,
                    available_topics=available_topics,
                )
                if task_type > 0
                else None
            )
            aggregates.append(
                ClassMistakeAggregate(
                    task_type=task_type,
                    topic=topic,
                    mistake_count=mistake_count,
                    affected_students=len(affected),
                )
            )

        return ClassOverview(
            total_students=len(student_ids),
            total_incorrect_steps=len(rows),
            by_type=aggregates,
        )

    async def _student_activity(self, student_id: uuid.UUID) -> StudentActivitySummary:
        tutor_sessions = await self._session.scalar(
            select(func.count())
            .select_from(TutorSession)
            .where(TutorSession.user_id == student_id)
        )
        completed_tests = await self._session.scalar(
            select(func.count())
            .select_from(TestSession)
            .where(
                TestSession.student_id == student_id,
                TestSession.status == TestSessionStatus.COMPLETED,
            )
        )
        submitted_homework = await self._session.scalar(
            select(func.count())
            .select_from(HomeworkAssignment)
            .where(
                HomeworkAssignment.student_id == student_id,
                HomeworkAssignment.status == HomeworkStatus.SUBMITTED,
            )
        )
        return StudentActivitySummary(
            tutor_sessions=int(tutor_sessions or 0),
            completed_test_sessions=int(completed_tests or 0),
            submitted_homework=int(submitted_homework or 0),
        )
