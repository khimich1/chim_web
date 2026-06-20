"""Homework assignment business logic."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    HomeworkAssignment,
    HomeworkItemProgress,
    HomeworkStatus,
    User,
    UserRole,
)
from app.models.enums import GradingMode, HomeworkItemKind
from app.core.config import Settings, get_settings
from app.repositories.app.homework_feedback_repo import HomeworkFeedbackRepository
from app.repositories.app.homework_repo import HomeworkRepository
from app.repositories.app.student_repo import StudentRepository
from app.repositories.app.teacher_theme_repo import TeacherThemeRepository
from app.repositories.app.test_session_repo import TestSessionRepository
from app.schemas.homework import (
    HomeworkCreate,
    HomeworkRead,
    HomeworkSubmissionStepRead,
    StepFeedbackEmbeddedRead,
)
from app.services.custom_test_session_service import _answer_image_url
from app.services.homework_mapper import to_homework_read
from app.services.homework_validation import validate_homework_items


class HomeworkService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._homework = HomeworkRepository(session)
        self._students = StudentRepository(session)
        self._test_sessions = TestSessionRepository(session)
        self._theme_repo = TeacherThemeRepository(session)
        self._feedback_repo = HomeworkFeedbackRepository(session)

    def _embed_feedback(
        self,
        feedback,
    ) -> StepFeedbackEmbeddedRead | None:
        if feedback is None or feedback.published_at is None:
            return None
        has_text = bool((feedback.teacher_text or "").strip())
        has_voice = feedback.teacher_voice_id is not None
        has_images = bool(feedback.teacher_image_ids)
        if not (has_text or has_voice or has_images):
            return None
        return StepFeedbackEmbeddedRead(
            teacher_text=feedback.teacher_text,
            teacher_voice_url=(
                f"/api/uploads/audio/{feedback.teacher_voice_id}"
                if feedback.teacher_voice_id
                else None
            ),
            teacher_image_urls=[
                f"/api/uploads/images/{image_id}"
                for image_id in feedback.teacher_image_ids
            ],
            published_at=feedback.published_at,
        )

    async def _submission_steps_for_teacher(
        self,
        assignment: HomeworkAssignment,
    ) -> list[HomeworkSubmissionStepRead]:
        submission = assignment.submission
        if submission is None or submission.test_session_id is None:
            return []

        test_session = await self._test_sessions.get_with_steps(submission.test_session_id)
        if test_session is None:
            return []

        steps_out: list[HomeworkSubmissionStepRead] = []
        for step in test_session.steps:
            if step.custom_task_id is None:
                continue
            task = await self._theme_repo.get_task_by_id(step.custom_task_id)
            if task is None or task.grading_mode != GradingMode.SELF_CHECK:
                continue
            step_feedback = await self._feedback_repo.get_step_feedback(step.id)
            steps_out.append(
                HomeworkSubmissionStepRead(
                    position=step.position,
                    custom_task_id=step.custom_task_id,
                    title=task.title,
                    grading_mode=task.grading_mode,
                    question_blocks=task.question_blocks,
                    reference_answer=task.reference_answer,
                    answer=step.answer,
                    answer_image_url=_answer_image_url(step.answer_image_id),
                    status=step.status,
                    feedback=self._embed_feedback(step_feedback),
                )
            )
        return steps_out

    async def _submission_feedback_for_teacher(
        self,
        assignment: HomeworkAssignment,
    ) -> StepFeedbackEmbeddedRead | None:
        submission = assignment.submission
        if submission is None:
            return None
        row = await self._feedback_repo.get_submission_feedback(submission.id)
        return self._embed_feedback(row)

    async def _has_teacher_feedback_flag(
        self,
        assignment_id: uuid.UUID,
    ) -> bool:
        return await self._feedback_repo.assignment_has_teacher_feedback(assignment_id)

    async def create_assignment(
        self,
        teacher: User,
        data: HomeworkCreate,
    ) -> HomeworkRead:
        student = await self._students.get_student_for_teacher(
            data.student_id,
            teacher.id,
        )
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        await validate_homework_items(
            data.items,
            track=student.student_profile.track,
            teacher_id=teacher.id,
            settings=self._settings,
            session=self._session,
        )

        items_payload = [item.model_dump(mode="json") for item in data.items]
        assignment = HomeworkAssignment(
            student_id=data.student_id,
            teacher_id=teacher.id,
            title=data.title,
            description=data.description,
            due_at=data.due_at,
            items=items_payload,
            status=HomeworkStatus.ASSIGNED,
            item_progress=[
                HomeworkItemProgress(
                    item_index=index,
                    kind=HomeworkItemKind(item["kind"]),
                    completed=False,
                )
                for index, item in enumerate(items_payload)
            ],
        )
        await self._homework.add(assignment)
        await self._session.commit()
        reloaded = await self._homework.get_by_id(assignment.id)
        assert reloaded is not None
        return to_homework_read(reloaded, include_student_email=True)

    async def list_assignments(self, user: User) -> list[HomeworkRead]:
        if user.role == UserRole.TEACHER:
            assignments = await self._homework.list_by_teacher(user.id)
            result: list[HomeworkRead] = []
            for assignment in assignments:
                has_fb = await self._has_teacher_feedback_flag(assignment.id)
                result.append(
                    to_homework_read(
                        assignment,
                        include_student_email=True,
                        has_teacher_feedback=has_fb,
                    )
                )
            return result
        assignments = await self._homework.list_by_student(user.id)
        result: list[HomeworkRead] = []
        for assignment in assignments:
            active_id = await self._active_session_id(user.id, assignment.id)
            has_fb = await self._has_teacher_feedback_flag(assignment.id)
            result.append(
                to_homework_read(
                    assignment,
                    active_test_session_id=active_id,
                    has_teacher_feedback=has_fb,
                )
            )
        return result

    async def _active_session_id(
        self,
        student_id: uuid.UUID,
        homework_assignment_id: uuid.UUID,
    ) -> uuid.UUID | None:
        active = await self._test_sessions.find_latest_active(
            student_id,
            homework_assignment_id=homework_assignment_id,
        )
        return active.id if active is not None else None

    async def get_assignment(self, user: User, assignment_id: uuid.UUID) -> HomeworkRead:
        assignment = await self._homework.get_by_id(assignment_id)
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Homework not found",
            )
        if user.role == UserRole.TEACHER:
            if assignment.teacher_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not your homework assignment",
                )
            return to_homework_read(
                assignment,
                include_student_email=True,
                active_test_session_id=None,
                submission_steps=await self._submission_steps_for_teacher(assignment),
                submission_feedback=await self._submission_feedback_for_teacher(assignment),
                has_teacher_feedback=await self._has_teacher_feedback_flag(assignment.id),
            )
        if assignment.student_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your homework assignment",
            )
        active_id = await self._active_session_id(user.id, assignment.id)
        return to_homework_read(
            assignment,
            active_test_session_id=active_id,
            has_teacher_feedback=await self._has_teacher_feedback_flag(assignment.id),
        )
