"""Stepik-style test session business logic.

Sessions live in the app DB; question content (text, correct answer, hint,
explanation) comes from the read-only content DB. `correct_ans` is never
returned to the client — only a boolean correctness result.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import (
    CustomTask,
    ExamTrack,
    HomeworkAssignment,
    HomeworkStatus,
    StepStatus,
    StudentProfile,
    TestSession,
    TestSessionStatus,
    TestSessionStep,
    User,
)
from app.models.enums import GradingMode, HomeworkItemKind, TestSessionSource
from app.repositories.app.homework_repo import HomeworkRepository
from app.repositories.app.teacher_theme_repo import TeacherThemeRepository
from app.repositories.app.test_session_repo import TestSessionRepository
from app.repositories.content.base import ContentDbError
from app.repositories.content.tests import ExamContentRepo, TestQuestion
from app.schemas.test_session import (
    ActiveSessionResponse,
    SessionCreate,
    SessionRead,
    SessionSummary,
    SessionSummaryStep,
    StepCheckResponse,
    StepCompareResponse,
    StepRead,
)
from app.services.activity_service import ActivityService
from app.services.custom_test_session_service import CustomTestSessionService
from app.services.grading_service import GradingService
from app.services.image_substitution import substitute_image_placeholders
from app.services.onboarding_service import OnboardingService

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _session_duration_minutes(created_at: datetime, completed_at: datetime) -> int:
    seconds = (
        _ensure_utc(completed_at) - _ensure_utc(created_at)
    ).total_seconds()
    if seconds <= 0:
        return 0
    return int(seconds // 60)


class TestSessionService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        activity: ActivityService | None = None,
    ) -> None:
        self._session = session
        self._settings = settings
        self._repo = TestSessionRepository(session)
        self._grading = GradingService()
        self._activity = activity or ActivityService(session)
        self._custom = CustomTestSessionService(session, settings, self._activity)
        self._content_repos = {
            ExamTrack.EGE: ExamContentRepo(settings.content_ege_db_path),
            ExamTrack.OGE: ExamContentRepo(settings.content_oge_db_path),
        }

    async def _run_activity_hook(
        self,
        hook_name: str,
        action: Callable[[], Awaitable[_T]],
    ) -> None:
        """Record gamification side effects without failing the primary flow."""
        try:
            await action()
            await self._session.commit()
        except Exception:
            logger.exception("Activity hook failed: %s", hook_name)
            await self._session.rollback()

    async def _resolve_track(self, student: User) -> ExamTrack:
        profile = await self._session.scalar(
            select(StudentProfile).where(StudentProfile.user_id == student.id)
        )
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found",
            )
        return profile.track

    def _content_repo(self, track: ExamTrack) -> ExamContentRepo:
        return self._content_repos[track]

    async def create_session(
        self, student: User, data: SessionCreate
    ) -> SessionRead:
        if data.custom_theme_id is not None:
            return await self._custom.create_session(student, data)

        track = await self._resolve_track(student)
        repo = self._content_repo(track)
        practice_task_type: int | None = None

        if data.homework_assignment_id is not None:
            exam_sources, custom_tasks = await self._resolve_homework_content(
                student, data.homework_assignment_id
            )
            sources = exam_sources
        else:
            if (data.variant_ref or "").strip():
                sources = [(data.variant_ref.strip(), data.types)]
                practice_task_type = None
            else:
                assert data.types is not None
                sources = repo.expand_types_across_variants(data.types, track=track)
                practice_task_type = (
                    data.types[0] if len(data.types) == 1 else None
                )
            custom_tasks = []

        questions = self._collect_questions(repo, sources) if sources else []
        if not questions and not custom_tasks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No questions found for the requested variant",
            )

        if data.homework_assignment_id is not None:
            distinct_variants = {variant for variant, _ in sources}
            variant_ref = (
                next(iter(distinct_variants)) if len(distinct_variants) == 1 else None
            )
        elif (data.variant_ref or "").strip():
            distinct_variants = {variant for variant, _ in sources}
            variant_ref = (
                next(iter(distinct_variants)) if len(distinct_variants) == 1 else None
            )
        else:
            variant_ref = None

        steps: list[TestSessionStep] = []
        position = 0
        for question in questions:
            steps.append(
                TestSessionStep(
                    position=position,
                    test_id=question.id,
                    status=StepStatus.UNSEEN,
                )
            )
            position += 1
        for task in custom_tasks:
            steps.append(
                TestSessionStep(
                    position=position,
                    custom_task_id=task.id,
                    status=StepStatus.UNSEEN,
                )
            )
            position += 1

        has_custom = len(custom_tasks) > 0
        has_exam = len(questions) > 0
        if has_custom and not has_exam:
            session_source = TestSessionSource.CUSTOM
            custom_theme_id = (
                custom_tasks[0].theme_id
                if len({task.theme_id for task in custom_tasks}) == 1
                else None
            )
        else:
            session_source = TestSessionSource.EXAM
            custom_theme_id = None

        custom_task_ids = [str(task.id) for task in custom_tasks] or None

        test_session = TestSession(
            student_id=student.id,
            track=track,
            source=session_source,
            variant_ref=variant_ref,
            practice_task_type=practice_task_type,
            homework_assignment_id=data.homework_assignment_id,
            custom_theme_id=custom_theme_id,
            custom_task_ids=custom_task_ids,
            status=TestSessionStatus.IN_PROGRESS,
            created_at=datetime.now(timezone.utc),
            steps=steps,
        )
        await self._repo.add(test_session)
        await OnboardingService(self._session, self._settings).mark_first_action(
            student.id,
            action_type="test_session",
        )
        await self._session.commit()

        reloaded = await self._repo.get_with_steps(test_session.id)
        assert reloaded is not None
        if session_source == TestSessionSource.CUSTOM:
            return await self._custom.to_session_read(reloaded)
        if has_custom:
            return await self._to_mixed_session_read(reloaded)
        return self._to_session_read(reloaded, repo)

    def _collect_questions(
        self,
        repo: ExamContentRepo,
        sources: list[tuple[str, list[int] | None]],
    ) -> list[TestQuestion]:
        """Gather (deduplicated) questions for one or more (variant, types) specs."""
        questions: list[TestQuestion] = []
        seen_ids: set[int] = set()
        for variant, types in sources:
            try:
                variant_questions = repo.list_questions(variant)
            except ContentDbError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Test content database unavailable",
                ) from exc
            if types is not None:
                wanted = set(types)
                variant_questions = [q for q in variant_questions if q.type in wanted]
            for question in variant_questions:
                if question.id in seen_ids:
                    continue
                seen_ids.add(question.id)
                questions.append(question)
        return questions

    async def _resolve_homework_content(
        self,
        student: User,
        homework_assignment_id: uuid.UUID,
    ) -> tuple[list[tuple[str, list[int] | None]], list[CustomTask]]:
        assignment = await self._load_homework_assignment(student, homework_assignment_id)

        track = await self._resolve_track(student)
        repo = self._content_repo(track)
        theme_repo = TeacherThemeRepository(self._session)
        exam_sources: list[tuple[str, list[int] | None]] = []
        custom_tasks: list[CustomTask] = []

        for item in assignment.items:
            kind = item.get("kind")
            if kind == HomeworkItemKind.TEST_VARIANT.value:
                exam_sources.append((item["variant"], None))
            elif kind == HomeworkItemKind.TEST_PARTIAL.value:
                exam_sources.append((item["variant"], list(item["types"])))
            elif kind == HomeworkItemKind.TEST_BY_TYPE.value:
                item_variants = item.get("variants")
                exam_sources.extend(
                    repo.expand_types_across_variants(
                        list(item["types"]),
                        track=track,
                        variants=item_variants,
                    )
                )
            elif kind == HomeworkItemKind.CUSTOM_THEME.value:
                custom_tasks.extend(
                    await self._resolve_custom_theme_tasks(
                        item,
                        teacher_id=assignment.teacher_id,
                        theme_repo=theme_repo,
                    )
                )

        if not exam_sources and not custom_tasks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Homework assignment has no test items",
            )
        return exam_sources, custom_tasks

    async def _load_homework_assignment(
        self,
        student: User,
        homework_assignment_id: uuid.UUID,
    ) -> HomeworkAssignment:
        assignment = await HomeworkRepository(self._session).get_by_id(
            homework_assignment_id
        )
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Homework not found",
            )
        if assignment.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your homework assignment",
            )
        if assignment.status == HomeworkStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Homework already submitted",
            )
        return assignment

    async def _resolve_custom_theme_tasks(
        self,
        item: dict,
        *,
        teacher_id: uuid.UUID,
        theme_repo: TeacherThemeRepository,
    ) -> list[CustomTask]:
        theme_id = uuid.UUID(str(item["theme_id"]))
        theme = await theme_repo.get_for_teacher(theme_id, teacher_id)
        if theme is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Theme not found",
            )
        tasks = await theme_repo.list_tasks(theme_id)
        if not tasks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Theme has no tasks",
            )
        ordered = sorted(tasks, key=lambda task: (task.sort_order, task.created_at))
        task_ids = item.get("task_ids")
        if task_ids is None:
            return ordered
        wanted = [str(task_id) for task_id in task_ids]
        by_id = {str(task.id): task for task in ordered}
        unknown = set(wanted) - set(by_id)
        if unknown:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="task_ids must belong to the theme",
            )
        return [by_id[str(task_id)] for task_id in wanted]

    async def get_active_session(
        self,
        student: User,
        *,
        variant_ref: str | None = None,
        homework_assignment_id: uuid.UUID | None = None,
        task_type: int | None = None,
        custom_theme_id: uuid.UUID | None = None,
    ) -> ActiveSessionResponse:
        has_variant = bool((variant_ref or "").strip())
        has_homework = homework_assignment_id is not None
        has_task_type = task_type is not None
        has_custom = custom_theme_id is not None
        scope_count = sum([has_variant, has_homework, has_task_type, has_custom])
        if scope_count != 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Provide exactly one of variant_ref, homework_assignment_id, "
                    "task_type, or custom_theme_id"
                ),
            )

        if homework_assignment_id is not None:
            assignment = await HomeworkRepository(self._session).get_by_id(
                homework_assignment_id
            )
            if assignment is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Homework not found",
                )
            if assignment.student_id != student.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not your homework assignment",
                )

        active = await self._repo.find_latest_active(
            student.id,
            variant_ref=variant_ref.strip() if has_variant else None,
            homework_assignment_id=homework_assignment_id,
            practice_task_type=task_type,
            custom_theme_id=custom_theme_id,
        )
        return ActiveSessionResponse(
            session_id=active.id if active is not None else None,
        )

    async def get_session(
        self, student: User, session_id: uuid.UUID
    ) -> SessionRead:
        test_session = await self._load_owned_session(student, session_id)
        has_custom = any(step.custom_task_id for step in test_session.steps)
        has_exam = any(step.test_id for step in test_session.steps)
        if has_custom and not has_exam:
            return await self._custom.to_session_read(test_session)
        if has_exam and not has_custom:
            repo = self._content_repo(test_session.track)
            return self._to_session_read(test_session, repo)
        return await self._to_mixed_session_read(test_session)

    async def check_step(
        self,
        student: User,
        session_id: uuid.UUID,
        position: int,
        answer: str,
    ) -> StepCheckResponse:
        test_session = await self._load_owned_session(student, session_id)
        step = self._find_step(test_session, position)
        if step.custom_task_id is not None:
            return await self._custom.check_step(
                student, session_id, position, answer
            )
        if test_session.status == TestSessionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Session already completed",
            )
        step = self._find_step(test_session, position)
        repo = self._content_repo(test_session.track)
        question = self._require_question(repo, step.test_id)

        was_already_correct = step.is_correct is True
        is_correct = self._grading.grade(answer, question.correct_ans)
        step.answer = answer
        step.is_correct = is_correct
        step.status = StepStatus.CHECKED
        step.checked_at = datetime.now(timezone.utc)
        await self._session.commit()

        if is_correct and not was_already_correct:
            step_id = step.id
            student_id = student.id
            await self._run_activity_hook(
                "record_step_correct",
                lambda: self._activity.record_step_correct(student_id, step_id),
            )

        return StepCheckResponse(
            position=step.position,
            is_correct=is_correct,
            status=step.status,
        )

    async def compare_step(
        self,
        student: User,
        session_id: uuid.UUID,
        position: int,
        answer: str,
    ) -> StepCompareResponse:
        return await self._custom.compare_step(
            student, session_id, position, answer
        )

    async def complete_session(
        self, student: User, session_id: uuid.UUID
    ) -> SessionSummary:
        test_session = await self._load_owned_session(student, session_id)
        has_custom = any(step.custom_task_id for step in test_session.steps)
        has_exam = any(step.test_id for step in test_session.steps)
        if has_custom and not has_exam:
            return await self._custom.complete_session(student, session_id)
        if has_custom and has_exam:
            return await self._complete_mixed_session(student, test_session)

        score = sum(1 for step in test_session.steps if step.is_correct)
        max_score = len(test_session.steps)

        was_already_completed = test_session.status == TestSessionStatus.COMPLETED
        completed_at = datetime.now(timezone.utc)
        if not was_already_completed:
            test_session.status = TestSessionStatus.COMPLETED
            test_session.completed_at = completed_at
        test_session.score = score
        test_session.max_score = max_score
        await self._session.commit()

        if not was_already_completed:
            minutes = _session_duration_minutes(test_session.created_at, completed_at)
            student_id = student.id
            await self._run_activity_hook(
                "add_session_minutes",
                lambda: self._activity.add_session_minutes(student_id, minutes),
            )

        repo = self._content_repo(test_session.track)
        summary_steps = [
            SessionSummaryStep(
                position=step.position,
                test_id=step.test_id,
                type=self._require_question(repo, step.test_id).type,
                is_correct=step.is_correct,
                hint_used=step.hint_used,
            )
            for step in test_session.steps
        ]
        return SessionSummary(
            id=test_session.id,
            status=test_session.status,
            score=score,
            max_score=max_score,
            completed_at=test_session.completed_at,
            steps=summary_steps,
        )

    async def _load_owned_session(
        self, student: User, session_id: uuid.UUID
    ) -> TestSession:
        test_session = await self._repo.get_with_steps(session_id)
        if test_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        if test_session.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your session",
            )
        return test_session

    @staticmethod
    def _find_step(test_session: TestSession, position: int) -> TestSessionStep:
        for step in test_session.steps:
            if step.position == position:
                return step
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )

    def _require_question(
        self, repo: ExamContentRepo, test_id: int
    ) -> TestQuestion:
        try:
            question = repo.get_question(test_id)
        except ContentDbError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Test content database unavailable",
            ) from exc
        if question is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question content not found",
            )
        return question

    async def _to_mixed_session_read(self, test_session: TestSession) -> SessionRead:
        repo = self._content_repo(test_session.track)
        theme_repo = TeacherThemeRepository(self._session)
        steps: list[StepRead] = []
        for step in test_session.steps:
            if step.custom_task_id is not None:
                task = await theme_repo.get_task_by_id(step.custom_task_id)
                if task is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Custom task not found",
                    )
                steps.append(
                    StepRead(
                        position=step.position,
                        custom_task_id=step.custom_task_id,
                        question_blocks=task.question_blocks,
                        grading_mode=task.grading_mode,
                        status=step.status,
                        answer=step.answer,
                        is_correct=step.is_correct,
                        hint_used=step.hint_used,
                    )
                )
            else:
                question = self._require_question(repo, step.test_id)
                steps.append(
                    StepRead(
                        position=step.position,
                        test_id=step.test_id,
                        type=question.type,
                        question=substitute_image_placeholders(question.question),
                        options=question.options,
                        status=step.status,
                        answer=step.answer,
                        is_correct=step.is_correct,
                        hint_used=step.hint_used,
                    )
                )
        return SessionRead(
            id=test_session.id,
            track=test_session.track,
            source=test_session.source,
            variant_ref=test_session.variant_ref,
            homework_assignment_id=test_session.homework_assignment_id,
            custom_theme_id=test_session.custom_theme_id,
            status=test_session.status,
            score=test_session.score,
            max_score=test_session.max_score,
            total_steps=len(steps),
            created_at=test_session.created_at,
            steps=steps,
        )

    async def _complete_mixed_session(
        self,
        student: User,
        test_session: TestSession,
    ) -> SessionSummary:
        repo = self._content_repo(test_session.track)
        theme_repo = TeacherThemeRepository(self._session)
        score = 0
        max_score = 0
        summary_steps: list[SessionSummaryStep] = []

        for step in test_session.steps:
            if step.custom_task_id is not None:
                task = await theme_repo.get_task_by_id(step.custom_task_id)
                if task is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Custom task not found",
                    )
                if task.grading_mode == GradingMode.AUTO:
                    max_score += 1
                    if step.is_correct:
                        score += 1
                summary_steps.append(
                    SessionSummaryStep(
                        position=step.position,
                        custom_task_id=step.custom_task_id,
                        grading_mode=task.grading_mode,
                        is_correct=step.is_correct,
                        hint_used=step.hint_used,
                    )
                )
            else:
                max_score += 1
                if step.is_correct:
                    score += 1
                summary_steps.append(
                    SessionSummaryStep(
                        position=step.position,
                        test_id=step.test_id,
                        type=self._require_question(repo, step.test_id).type,
                        is_correct=step.is_correct,
                        hint_used=step.hint_used,
                    )
                )

        was_already_completed = test_session.status == TestSessionStatus.COMPLETED
        completed_at = datetime.now(timezone.utc)
        if not was_already_completed:
            test_session.status = TestSessionStatus.COMPLETED
            test_session.completed_at = completed_at
        test_session.score = score
        test_session.max_score = max_score
        await self._session.commit()

        if not was_already_completed:
            minutes = _session_duration_minutes(test_session.created_at, completed_at)
            student_id = student.id
            await self._run_activity_hook(
                "add_session_minutes",
                lambda: self._activity.add_session_minutes(student_id, minutes),
            )

        return SessionSummary(
            id=test_session.id,
            status=test_session.status,
            score=score,
            max_score=max_score,
            completed_at=test_session.completed_at,
            steps=summary_steps,
        )

    def _to_session_read(
        self, test_session: TestSession, repo: ExamContentRepo
    ) -> SessionRead:
        steps: list[StepRead] = []
        for step in test_session.steps:
            question = self._require_question(repo, step.test_id)
            steps.append(
                StepRead(
                    position=step.position,
                    test_id=step.test_id,
                    type=question.type,
                    question=substitute_image_placeholders(question.question),
                    options=question.options,
                    status=step.status,
                    answer=step.answer,
                    is_correct=step.is_correct,
                    hint_used=step.hint_used,
                )
            )
        return SessionRead(
            id=test_session.id,
            track=test_session.track,
            source=test_session.source,
            variant_ref=test_session.variant_ref,
            homework_assignment_id=test_session.homework_assignment_id,
            custom_theme_id=test_session.custom_theme_id,
            status=test_session.status,
            score=test_session.score,
            max_score=test_session.max_score,
            total_steps=len(steps),
            created_at=test_session.created_at,
            steps=steps,
        )
