"""Custom theme test session adapter (SPEC §1.9.5, Task 69 / 97)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import (
    CustomTask,
    StepStatus,
    StudentProfile,
    TestSession,
    TestSessionSource,
    TestSessionStatus,
    TestSessionStep,
    User,
)
from app.models.enums import GradingMode
from app.repositories.app.teacher_theme_repo import TeacherThemeRepository
from app.schemas.custom_theme import CustomThemeListItem
from app.schemas.test_session import (
    SessionCreate,
    SessionRead,
    SessionSummary,
    SessionSummaryStep,
    StepAttachAnswerImageResponse,
    StepCheckResponse,
    StepCompareResponse,
    StepRead,
)
from app.services.activity_service import ActivityService
from app.services.onboarding_service import OnboardingService
from app.services.test_session.common import (
    SessionAdapterBase,
    answer_image_url,
    session_duration_minutes,
)


class CustomSessionAdapter(SessionAdapterBase):
    """Create, read, check, compare, and complete custom-theme sessions."""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        activity: ActivityService | None = None,
    ) -> None:
        super().__init__(session, settings, activity)
        self._theme_repo = TeacherThemeRepository(session)

    async def list_published_themes(
        self,
        student: User,
    ) -> list[CustomThemeListItem]:
        profile = await self._require_student_profile(student)
        themes = await self._theme_repo.list_published_by_teacher(profile.teacher_id)
        return [
            CustomThemeListItem(
                id=theme.id,
                title=theme.title,
                description=theme.description,
                task_count=len(theme.tasks),
                sort_order=theme.sort_order,
            )
            for theme in themes
        ]

    async def create_session(
        self,
        student: User,
        data: SessionCreate,
    ) -> SessionRead:
        assert data.custom_theme_id is not None
        profile = await self._require_student_profile(student)
        theme = await self._theme_repo.get_published_for_student(
            data.custom_theme_id,
            profile.teacher_id,
        )
        if theme is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Theme not found",
            )

        tasks = sorted(theme.tasks, key=lambda task: (task.sort_order, task.created_at))
        if not tasks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Theme has no tasks",
            )

        if data.task_ids is not None:
            wanted = {str(task_id) for task_id in data.task_ids}
            tasks_by_id = {str(task.id): task for task in tasks}
            unknown = wanted - set(tasks_by_id)
            if unknown:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="task_ids must belong to the theme",
                )
            tasks = [tasks_by_id[str(task_id)] for task_id in data.task_ids]

        test_session = TestSession(
            student_id=student.id,
            track=profile.track,
            source=TestSessionSource.CUSTOM,
            custom_theme_id=theme.id,
            custom_task_ids=[str(task.id) for task in tasks],
            status=TestSessionStatus.IN_PROGRESS,
            created_at=datetime.now(timezone.utc),
            steps=[
                TestSessionStep(
                    position=index,
                    custom_task_id=task.id,
                    status=StepStatus.UNSEEN,
                )
                for index, task in enumerate(tasks)
            ],
        )
        await self._repo.add(test_session)
        await OnboardingService(self._session, self._settings).mark_first_action(
            student.id,
            action_type="test_session",
        )
        await self._session.commit()

        reloaded = await self._repo.get_with_steps(test_session.id)
        assert reloaded is not None
        return await self.to_session_read(reloaded)

    async def check_step(
        self,
        student: User,
        session_id: uuid.UUID,
        position: int,
        answer: str,
    ) -> StepCheckResponse:
        test_session = await self._load_owned_custom_session(student, session_id)
        if test_session.status == TestSessionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Session already completed",
            )
        step = self.find_step(test_session, position)
        task = await self._require_task(step)
        if task.grading_mode != GradingMode.AUTO:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Use compare for self_check steps",
            )
        assert task.correct_value is not None

        was_already_correct = step.is_correct is True
        is_correct = self._grading.grade(answer, task.correct_value)
        step.answer = answer
        step.is_correct = is_correct
        step.status = StepStatus.CHECKED
        step.checked_at = datetime.now(timezone.utc)
        await self._session.commit()

        if is_correct and not was_already_correct:
            step_id = step.id
            student_id = student.id
            await self.run_activity_hook(
                "record_step_correct",
                lambda: self._activity.record_step_correct(student_id, step_id),
            )

        return StepCheckResponse(
            position=step.position,
            is_correct=is_correct,
            status=step.status,
        )

    async def attach_answer_image(
        self,
        student: User,
        session_id: uuid.UUID,
        position: int,
        answer_image_id: uuid.UUID,
    ) -> StepAttachAnswerImageResponse:
        test_session = await self._load_owned_custom_session(student, session_id)
        if test_session.status == TestSessionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Session already completed",
            )
        if test_session.homework_assignment_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Answer image upload is only required for homework sessions",
            )

        step = self.find_step(test_session, position)
        task = await self._require_task(step)
        if task.grading_mode != GradingMode.SELF_CHECK:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Answer image is only for self_check steps",
            )
        if step.status == StepStatus.CHECKED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot replace photo after compare",
            )

        image = await self._upload_repo.get_by_id(answer_image_id)
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            )
        if image.owner_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your image",
            )

        step.answer_image_id = answer_image_id
        await self._session.commit()

        return StepAttachAnswerImageResponse(
            position=step.position,
            answer_image_id=answer_image_id,
            answer_image_url=answer_image_url(answer_image_id),
        )

    async def compare_step(
        self,
        student: User,
        session_id: uuid.UUID,
        position: int,
        answer: str,
    ) -> StepCompareResponse:
        test_session = await self._load_owned_custom_session(student, session_id)
        if test_session.status == TestSessionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Session already completed",
            )
        step = self.find_step(test_session, position)
        task = await self._require_task(step)
        if task.grading_mode != GradingMode.SELF_CHECK:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Use check for auto steps",
            )
        if not task.reference_answer:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Task has no reference answer",
            )
        if step.status == StepStatus.CHECKED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Step already checked",
            )
        if test_session.homework_assignment_id is not None and step.answer_image_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Answer image is required for self_check homework steps",
            )

        step.answer = answer
        step.status = StepStatus.CHECKED
        step.checked_at = datetime.now(timezone.utc)
        await self._session.commit()

        return StepCompareResponse(
            position=step.position,
            status=step.status,
            reference_answer=task.reference_answer,
        )

    async def complete_session(
        self,
        student: User,
        session_id: uuid.UUID,
    ) -> SessionSummary:
        test_session = await self._load_owned_custom_session(student, session_id)
        tasks_by_step = await self._load_tasks_for_session(test_session)

        auto_steps = [
            step
            for step in test_session.steps
            if tasks_by_step[step.id].grading_mode == GradingMode.AUTO
        ]
        score = sum(1 for step in auto_steps if step.is_correct)
        max_score = len(auto_steps)

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

        summary_steps = [
            SessionSummaryStep(
                position=step.position,
                custom_task_id=step.custom_task_id,
                grading_mode=tasks_by_step[step.id].grading_mode,
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

    async def to_session_read(self, test_session: TestSession) -> SessionRead:
        tasks_by_step = await self._load_tasks_for_session(test_session)
        steps: list[StepRead] = []
        for step in test_session.steps:
            task = tasks_by_step[step.id]
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
        return SessionRead(
            id=test_session.id,
            track=test_session.track,
            source=TestSessionSource.CUSTOM,
            custom_theme_id=test_session.custom_theme_id,
            homework_assignment_id=test_session.homework_assignment_id,
            status=test_session.status,
            score=test_session.score,
            max_score=test_session.max_score,
            total_steps=len(steps),
            created_at=test_session.created_at,
            steps=steps,
        )

    async def _load_owned_custom_session(
        self,
        student: User,
        session_id: uuid.UUID,
    ) -> TestSession:
        test_session = await self.load_owned_session(student, session_id)
        if test_session.source != TestSessionSource.CUSTOM:
            has_custom = any(step.custom_task_id for step in test_session.steps)
            if not has_custom:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Not a custom session",
                )
        return test_session

    async def _require_student_profile(self, student: User) -> StudentProfile:
        profile = await self._session.scalar(
            select(StudentProfile).where(StudentProfile.user_id == student.id)
        )
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found",
            )
        return profile

    async def _require_task(self, step: TestSessionStep) -> CustomTask:
        if step.custom_task_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Custom task not found",
            )
        task = await self._theme_repo.get_task_by_id(step.custom_task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Custom task not found",
            )
        return task

    async def _load_tasks_for_session(
        self,
        test_session: TestSession,
    ) -> dict[uuid.UUID, CustomTask]:
        tasks_by_step: dict[uuid.UUID, CustomTask] = {}
        for step in test_session.steps:
            task = await self._require_task(step)
            tasks_by_step[step.id] = task
        return tasks_by_step
