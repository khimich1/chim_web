"""Test session facade — routes to exam / homework / custom adapters."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import User
from app.schemas.test_session import (
    ActiveSessionResponse,
    SessionCreate,
    SessionRead,
    SessionSummary,
    StepAttachAnswerImageResponse,
    StepCheckResponse,
    StepCompareResponse,
)
from app.services.activity_service import ActivityService
from app.services.test_session.common import session_duration_minutes
from app.services.test_session.custom_adapter import CustomSessionAdapter
from app.services.test_session.exam_adapter import ExamSessionAdapter
from app.services.test_session.homework_adapter import HomeworkSessionAdapter

# Backward-compatible re-exports for tests and legacy imports.
_session_duration_minutes = session_duration_minutes


class TestSessionService:
    """Facade over exam, homework, and custom session adapters."""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        activity: ActivityService | None = None,
    ) -> None:
        self._session = session
        self._settings = settings
        self._activity = activity or ActivityService(session)
        self._custom = CustomSessionAdapter(session, settings, self._activity)
        self._exam = ExamSessionAdapter(session, settings, self._activity)
        self._homework = HomeworkSessionAdapter(
            session,
            settings,
            self._activity,
            exam=self._exam,
            custom=self._custom,
        )
        self._repo = self._exam._repo

    async def create_session(
        self, student: User, data: SessionCreate
    ) -> SessionRead:
        if data.custom_theme_id is not None:
            return await self._custom.create_session(student, data)
        if data.homework_assignment_id is not None:
            return await self._homework.create_session(student, data)
        return await self._exam.create_session(student, data)

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
            await self._homework.assert_student_assignment(
                student, homework_assignment_id
            )

        active = await self._repo.find_latest_active(
            student.id,
            variant_ref=variant_ref.strip() if variant_ref is not None else None,
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
        test_session = await self._exam.load_owned_session(student, session_id)
        has_custom = any(step.custom_task_id for step in test_session.steps)
        has_exam = any(step.test_id for step in test_session.steps)
        if has_custom and not has_exam:
            return await self._custom.to_session_read(test_session)
        if has_exam and not has_custom:
            repo = self._exam.content_repo(test_session.track)
            return self._exam.to_session_read(test_session, repo)
        return await self._homework.to_mixed_session_read(test_session)

    async def check_step(
        self,
        student: User,
        session_id: uuid.UUID,
        position: int,
        answer: str,
    ) -> StepCheckResponse:
        test_session = await self._exam.load_owned_session(student, session_id)
        step = self._exam.find_step(test_session, position)
        if step.custom_task_id is not None:
            return await self._custom.check_step(
                student, session_id, position, answer
            )
        return await self._exam.check_step(student, test_session, position, answer)

    async def attach_answer_image(
        self,
        student: User,
        session_id: uuid.UUID,
        position: int,
        answer_image_id: uuid.UUID,
    ) -> StepAttachAnswerImageResponse:
        test_session = await self._exam.load_owned_session(student, session_id)
        step = self._exam.find_step(test_session, position)
        if step.custom_task_id is not None:
            return await self._custom.attach_answer_image(
                student,
                session_id,
                position,
                answer_image_id,
            )
        return await self._exam.attach_answer_image(
            student,
            test_session,
            step,
            answer_image_id,
        )

    async def compare_step(
        self,
        student: User,
        session_id: uuid.UUID,
        position: int,
        answer: str,
    ) -> StepCompareResponse:
        test_session = await self._exam.load_owned_session(student, session_id)
        step = self._exam.find_step(test_session, position)
        if step.custom_task_id is not None:
            return await self._custom.compare_step(
                student, session_id, position, answer
            )
        return await self._exam.compare_step(student, test_session, step, answer)

    async def complete_session(
        self, student: User, session_id: uuid.UUID
    ) -> SessionSummary:
        test_session = await self._exam.load_owned_session(student, session_id)
        has_custom = any(step.custom_task_id for step in test_session.steps)
        has_exam = any(step.test_id for step in test_session.steps)
        if has_custom and not has_exam:
            return await self._custom.complete_session(student, session_id)
        if has_custom and has_exam:
            return await self._homework.complete_mixed_session(student, test_session)
        return await self._exam.complete_session(student, test_session)
