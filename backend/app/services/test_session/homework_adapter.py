"""Homework assignment test session adapter — mixed exam + custom content."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import (
    CustomTask,
    HomeworkAssignment,
    HomeworkStatus,
    StepStatus,
    TestSession,
    TestSessionStatus,
    TestSessionStep,
    User,
)
from app.models.enums import GradingMode, HomeworkItemKind, TestSessionSource
from app.repositories.app.homework_repo import HomeworkRepository
from app.repositories.app.teacher_theme_repo import TeacherThemeRepository
from app.schemas.test_session import (
    SessionCreate,
    SessionRead,
    SessionSummary,
    SessionSummaryStep,
    StepRead,
)
from app.services.activity_service import ActivityService
from app.services.onboarding_service import OnboardingService
from app.services.test_session.common import (
    SessionAdapterBase,
    answer_image_url,
    session_duration_minutes,
)
from app.services.test_session.custom_adapter import CustomSessionAdapter
from app.services.test_session.exam_adapter import ExamSessionAdapter


class HomeworkSessionAdapter(SessionAdapterBase):
    """Sessions tied to homework assignments (exam, custom, or mixed items)."""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        activity: ActivityService | None = None,
        *,
        exam: ExamSessionAdapter | None = None,
        custom: CustomSessionAdapter | None = None,
    ) -> None:
        super().__init__(session, settings, activity)
        self._exam = exam or ExamSessionAdapter(session, settings, activity)
        self._custom = custom or CustomSessionAdapter(session, settings, activity)

    async def assert_student_assignment(
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
        return assignment

    async def create_session(
        self,
        student: User,
        data: SessionCreate,
    ) -> SessionRead:
        assert data.homework_assignment_id is not None
        exam_sources, custom_tasks = await self.resolve_homework_content(
            student, data.homework_assignment_id
        )

        track = await self.resolve_track(student)
        repo = self._exam.content_repo(track)
        questions = (
            self._exam.collect_questions(repo, exam_sources) if exam_sources else []
        )
        if not questions and not custom_tasks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No questions found for the requested variant",
            )

        distinct_variants = {variant for variant, _ in exam_sources}
        variant_ref = (
            next(iter(distinct_variants)) if len(distinct_variants) == 1 else None
        )

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
            return await self.to_mixed_session_read(reloaded)
        return self._exam.to_session_read(reloaded, repo)

    async def resolve_homework_content(
        self,
        student: User,
        homework_assignment_id: uuid.UUID,
    ) -> tuple[list[tuple[str, list[int] | None]], list[CustomTask]]:
        assignment = await self.load_homework_assignment(student, homework_assignment_id)

        track = await self.resolve_track(student)
        repo = self._exam.content_repo(track)
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
                    await self.resolve_custom_theme_tasks(
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

    async def load_homework_assignment(
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

    async def resolve_custom_theme_tasks(
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

    async def to_mixed_session_read(self, test_session: TestSession) -> SessionRead:
        repo = self._exam.content_repo(test_session.track)
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
                        answer_image_id=step.answer_image_id,
                        answer_image_url=answer_image_url(step.answer_image_id),
                        is_correct=step.is_correct,
                        hint_used=step.hint_used,
                    )
                )
            else:
                steps.append(self._exam.exam_step_read(test_session, step, repo))
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

    async def complete_mixed_session(
        self,
        student: User,
        test_session: TestSession,
    ) -> SessionSummary:
        repo = self._exam.content_repo(test_session.track)
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
                step_max, step_score = self._exam.exam_step_score(
                    test_session, step, repo
                )
                max_score += step_max
                score += step_score
                summary_steps.append(
                    self._exam.exam_summary_step(test_session, step, repo)
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
            minutes = session_duration_minutes(test_session.created_at, completed_at)
            student_id = student.id
            await self.run_activity_hook(
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
