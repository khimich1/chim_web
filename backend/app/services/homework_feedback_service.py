"""Teacher/student homework feedback business logic (SPEC §1.9.9)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models import TestSessionStep, User
from app.models.enums import ExamTrack, GradingMode
from app.repositories.app.homework_feedback_repo import HomeworkFeedbackRepository
from app.repositories.app.teacher_theme_repo import TeacherThemeRepository
from app.repositories.app.test_session_repo import TestSessionRepository
from app.repositories.app.upload_repo import UploadedAudioRepository, UploadedImageRepository
from app.repositories.content.tests import ExamContentRepo
from app.schemas.homework_feedback import (
    FeedbackContentRead,
    StepFeedbackRead,
    StepFeedbackUpsert,
    StudentHomeworkFeedbackRead,
    SubmissionFeedbackUpsert,
)
from app.services.content_grading import get_content_grading_mode


def _has_content(
    *,
    teacher_text: str | None,
    teacher_voice_id: uuid.UUID | None,
    teacher_image_ids: list[uuid.UUID],
) -> bool:
    text = (teacher_text or "").strip()
    return bool(text or teacher_voice_id or teacher_image_ids)


def _voice_url(voice_id: uuid.UUID | None) -> str | None:
    if voice_id is None:
        return None
    return f"/api/uploads/audio/{voice_id}"


def _image_urls(image_ids: list[str]) -> list[str]:
    return [f"/api/uploads/images/{image_id}" for image_id in image_ids]


class HomeworkFeedbackService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._feedback = HomeworkFeedbackRepository(session)
        self._themes = TeacherThemeRepository(session)
        self._sessions = TestSessionRepository(session)
        self._images = UploadedImageRepository(session)
        self._audio = UploadedAudioRepository(session)
        self._content_repos = {
            ExamTrack.EGE: ExamContentRepo(self._settings.content_ege_db_path),
            ExamTrack.OGE: ExamContentRepo(self._settings.content_oge_db_path),
        }

    def _content_repo(self, track: ExamTrack) -> ExamContentRepo:
        return self._content_repos[track]

    async def _step_is_self_check(
        self,
        step: TestSessionStep,
        track: ExamTrack,
    ) -> bool:
        if step.custom_task_id is not None:
            task = await self._themes.get_task_by_id(step.custom_task_id)
            return task is not None and task.grading_mode == GradingMode.SELF_CHECK
        if step.test_id is not None:
            question = self._content_repo(track).get_question(step.test_id)
            if question is None:
                return False
            return get_content_grading_mode(track, question.type) == "self_check"
        return False

    async def _step_title(
        self,
        step: TestSessionStep,
        track: ExamTrack,
    ) -> str | None:
        if step.custom_task_id is not None:
            task = await self._themes.get_task_by_id(step.custom_task_id)
            return task.title if task else None
        if step.test_id is not None:
            question = self._content_repo(track).get_question(step.test_id)
            return f"Задание {question.type}" if question else None
        return None

    async def upsert_step_feedback(
        self,
        teacher: User,
        assignment_id: uuid.UUID,
        position: int,
        data: StepFeedbackUpsert,
    ) -> StepFeedbackRead:
        assignment = await self._feedback.get_submitted_assignment_for_teacher(
            assignment_id,
            teacher.id,
        )
        if assignment is None or assignment.submission is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submitted homework not found",
            )

        step = await self._feedback.get_step_for_assignment_position(
            assignment_id,
            position,
        )
        if step is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Step not found in submission",
            )

        session_id = assignment.submission.test_session_id
        if session_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Homework submission has no test session",
            )

        test_session = await self._sessions.get_with_steps(session_id)
        if test_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test session not found",
            )

        if not await self._step_is_self_check(step, test_session.track):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Feedback is only allowed for self_check steps",
            )

        if not _has_content(
            teacher_text=data.teacher_text,
            teacher_voice_id=data.teacher_voice_id,
            teacher_image_ids=data.teacher_image_ids,
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one of text, voice, or images is required",
            )

        await self._validate_assets(teacher, data)

        now = datetime.now(timezone.utc)
        row = await self._feedback.upsert_step_feedback(
            test_session_step_id=step.id,
            teacher_text=(data.teacher_text or "").strip() or None,
            teacher_voice_id=data.teacher_voice_id,
            teacher_image_ids=[str(image_id) for image_id in data.teacher_image_ids],
            published_at=now,
        )
        await self._session.commit()

        title = await self._step_title(step, test_session.track)

        return StepFeedbackRead(
            position=position,
            title=title,
            teacher_text=row.teacher_text,
            teacher_voice_url=_voice_url(row.teacher_voice_id),
            teacher_image_urls=_image_urls(row.teacher_image_ids),
            published_at=row.published_at,
        )

    async def upsert_submission_feedback(
        self,
        teacher: User,
        assignment_id: uuid.UUID,
        data: SubmissionFeedbackUpsert,
    ) -> FeedbackContentRead:
        assignment = await self._feedback.get_submitted_assignment_for_teacher(
            assignment_id,
            teacher.id,
        )
        if assignment is None or assignment.submission is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submitted homework not found",
            )

        if not _has_content(
            teacher_text=data.teacher_text,
            teacher_voice_id=data.teacher_voice_id,
            teacher_image_ids=data.teacher_image_ids,
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one of text, voice, or images is required",
            )

        await self._validate_assets(teacher, data)

        now = datetime.now(timezone.utc)
        row = await self._feedback.upsert_submission_feedback(
            homework_submission_id=assignment.submission.id,
            teacher_text=(data.teacher_text or "").strip() or None,
            teacher_voice_id=data.teacher_voice_id,
            teacher_image_ids=[str(image_id) for image_id in data.teacher_image_ids],
            published_at=now,
        )
        await self._session.commit()

        return FeedbackContentRead(
            teacher_text=row.teacher_text,
            teacher_voice_url=_voice_url(row.teacher_voice_id),
            teacher_image_urls=_image_urls(row.teacher_image_ids),
            published_at=row.published_at,
        )

    async def get_student_feedback(
        self,
        student: User,
        assignment_id: uuid.UUID,
    ) -> StudentHomeworkFeedbackRead:
        assignment = await self._feedback.get_submitted_assignment_for_student(
            assignment_id,
            student.id,
        )
        if assignment is None or assignment.submission is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submitted homework not found",
            )

        step_rows = await self._feedback.list_step_feedbacks_for_assignment(assignment_id)
        session_id = assignment.submission.test_session_id
        if session_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Homework submission has no test session",
            )

        test_session = await self._sessions.get_with_steps(session_id)
        if test_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test session not found",
            )

        steps_out: list[StepFeedbackRead] = []
        for step, feedback in step_rows:
            if not await self._step_is_self_check(step, test_session.track):
                continue
            if feedback is None or feedback.published_at is None:
                continue
            if not _has_content(
                teacher_text=feedback.teacher_text,
                teacher_voice_id=feedback.teacher_voice_id,
                teacher_image_ids=[
                    uuid.UUID(image_id) for image_id in feedback.teacher_image_ids
                ],
            ):
                continue
            steps_out.append(
                StepFeedbackRead(
                    position=step.position,
                    title=await self._step_title(step, test_session.track),
                    teacher_text=feedback.teacher_text,
                    teacher_voice_url=_voice_url(feedback.teacher_voice_id),
                    teacher_image_urls=_image_urls(feedback.teacher_image_ids),
                    published_at=feedback.published_at,
                )
            )

        submission_feedback = None
        sub_row = await self._feedback.get_submission_feedback(assignment.submission.id)
        if sub_row is not None and sub_row.published_at is not None:
            if _has_content(
                teacher_text=sub_row.teacher_text,
                teacher_voice_id=sub_row.teacher_voice_id,
                teacher_image_ids=[
                    uuid.UUID(image_id) for image_id in sub_row.teacher_image_ids
                ],
            ):
                submission_feedback = FeedbackContentRead(
                    teacher_text=sub_row.teacher_text,
                    teacher_voice_url=_voice_url(sub_row.teacher_voice_id),
                    teacher_image_urls=_image_urls(sub_row.teacher_image_ids),
                    published_at=sub_row.published_at,
                )

        has_feedback = bool(steps_out or submission_feedback)
        return StudentHomeworkFeedbackRead(
            has_feedback=has_feedback,
            steps=steps_out,
            submission=submission_feedback,
        )

    async def has_teacher_feedback(self, assignment_id: uuid.UUID) -> bool:
        return await self._feedback.assignment_has_teacher_feedback(assignment_id)

    async def _validate_assets(
        self,
        teacher: User,
        data: StepFeedbackUpsert | SubmissionFeedbackUpsert,
    ) -> None:
        if data.teacher_voice_id is not None:
            audio = await self._audio.get_by_id(data.teacher_voice_id)
            if audio is None or audio.owner_id != teacher.id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid teacher voice upload",
                )

        for image_id in data.teacher_image_ids:
            image = await self._images.get_by_id(image_id)
            if image is None or image.owner_id != teacher.id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid teacher image upload",
                )
