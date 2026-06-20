"""Data access for UploadedImage rows (app DB)."""

from __future__ import annotations

import uuid

from sqlalchemy import cast, select, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    HomeworkAssignment,
    HomeworkSubmission,
    HomeworkSubmissionFeedback,
    TestSession,
    TestSessionStep,
    TestSessionStepFeedback,
    UploadedAudio,
    UploadedImage,
)


class UploadedImageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _image_id_in_json_array(column, image_id: uuid.UUID):
        return cast(column, String).like(f'%"{image_id}"%')

    async def create(
        self,
        *,
        owner_id: uuid.UUID,
        stored_filename: str,
        mime_type: str,
        size_bytes: int,
    ) -> UploadedImage:
        image = UploadedImage(
            owner_id=owner_id,
            stored_filename=stored_filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
        )
        self._session.add(image)
        await self._session.flush()
        return image

    async def get_by_id(self, image_id: uuid.UUID) -> UploadedImage | None:
        return await self._session.get(UploadedImage, image_id)

    async def teacher_can_view_answer_image(
        self,
        teacher_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> bool:
        stmt = (
            select(TestSessionStep.id)
            .join(TestSession, TestSessionStep.session_id == TestSession.id)
            .join(
                HomeworkAssignment,
                HomeworkAssignment.id == TestSession.homework_assignment_id,
            )
            .where(
                TestSessionStep.answer_image_id == image_id,
                HomeworkAssignment.teacher_id == teacher_id,
            )
            .limit(1)
        )
        return await self._session.scalar(stmt) is not None

    async def teacher_can_view_feedback_image(
        self,
        teacher_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> bool:
        """Teacher uploaded feedback images attached to their student's homework."""
        step_stmt = (
            select(TestSessionStepFeedback.id)
            .join(
                TestSessionStep,
                TestSessionStep.id == TestSessionStepFeedback.test_session_step_id,
            )
            .join(TestSession, TestSession.id == TestSessionStep.session_id)
            .join(
                HomeworkAssignment,
                HomeworkAssignment.id == TestSession.homework_assignment_id,
            )
            .where(
                HomeworkAssignment.teacher_id == teacher_id,
                self._image_id_in_json_array(
                    TestSessionStepFeedback.teacher_image_ids,
                    image_id,
                ),
            )
            .limit(1)
        )
        if await self._session.scalar(step_stmt) is not None:
            return True

        sub_stmt = (
            select(HomeworkSubmissionFeedback.id)
            .join(
                HomeworkSubmission,
                HomeworkSubmission.id == HomeworkSubmissionFeedback.homework_submission_id,
            )
            .join(
                HomeworkAssignment,
                HomeworkAssignment.id == HomeworkSubmission.assignment_id,
            )
            .where(
                HomeworkAssignment.teacher_id == teacher_id,
                self._image_id_in_json_array(
                    HomeworkSubmissionFeedback.teacher_image_ids,
                    image_id,
                ),
            )
            .limit(1)
        )
        return await self._session.scalar(sub_stmt) is not None

    async def student_can_view_image(
        self,
        student_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> bool:
        """Student answer images or teacher feedback images on their homework."""
        answer_stmt = (
            select(TestSessionStep.id)
            .join(TestSession, TestSessionStep.session_id == TestSession.id)
            .join(
                HomeworkAssignment,
                HomeworkAssignment.id == TestSession.homework_assignment_id,
            )
            .where(
                TestSessionStep.answer_image_id == image_id,
                HomeworkAssignment.student_id == student_id,
            )
            .limit(1)
        )
        if await self._session.scalar(answer_stmt) is not None:
            return True

        step_fb_stmt = (
            select(TestSessionStepFeedback.id)
            .join(
                TestSessionStep,
                TestSessionStep.id == TestSessionStepFeedback.test_session_step_id,
            )
            .join(TestSession, TestSession.id == TestSessionStep.session_id)
            .join(
                HomeworkAssignment,
                HomeworkAssignment.id == TestSession.homework_assignment_id,
            )
            .where(
                HomeworkAssignment.student_id == student_id,
                self._image_id_in_json_array(
                    TestSessionStepFeedback.teacher_image_ids,
                    image_id,
                ),
                TestSessionStepFeedback.published_at.is_not(None),
            )
            .limit(1)
        )
        if await self._session.scalar(step_fb_stmt) is not None:
            return True

        sub_fb_stmt = (
            select(HomeworkSubmissionFeedback.id)
            .join(
                HomeworkSubmission,
                HomeworkSubmission.id == HomeworkSubmissionFeedback.homework_submission_id,
            )
            .join(
                HomeworkAssignment,
                HomeworkAssignment.id == HomeworkSubmission.assignment_id,
            )
            .where(
                HomeworkAssignment.student_id == student_id,
                self._image_id_in_json_array(
                    HomeworkSubmissionFeedback.teacher_image_ids,
                    image_id,
                ),
                HomeworkSubmissionFeedback.published_at.is_not(None),
            )
            .limit(1)
        )
        return await self._session.scalar(sub_fb_stmt) is not None


class UploadedAudioRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        owner_id: uuid.UUID,
        stored_filename: str,
        mime_type: str,
        size_bytes: int,
        duration_sec: float | None,
    ) -> UploadedAudio:
        audio = UploadedAudio(
            owner_id=owner_id,
            stored_filename=stored_filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            duration_sec=duration_sec,
        )
        self._session.add(audio)
        await self._session.flush()
        return audio

    async def get_by_id(self, audio_id: uuid.UUID) -> UploadedAudio | None:
        return await self._session.get(UploadedAudio, audio_id)

    async def teacher_can_view_audio(
        self,
        teacher_id: uuid.UUID,
        audio_id: uuid.UUID,
    ) -> bool:
        audio = await self.get_by_id(audio_id)
        if audio is None:
            return False
        if audio.owner_id == teacher_id:
            return True

        step_stmt = (
            select(TestSessionStepFeedback.id)
            .join(
                TestSessionStep,
                TestSessionStep.id == TestSessionStepFeedback.test_session_step_id,
            )
            .join(TestSession, TestSession.id == TestSessionStep.session_id)
            .join(
                HomeworkAssignment,
                HomeworkAssignment.id == TestSession.homework_assignment_id,
            )
            .where(
                HomeworkAssignment.teacher_id == teacher_id,
                TestSessionStepFeedback.teacher_voice_id == audio_id,
            )
            .limit(1)
        )
        if await self._session.scalar(step_stmt) is not None:
            return True

        sub_stmt = (
            select(HomeworkSubmissionFeedback.id)
            .join(
                HomeworkSubmission,
                HomeworkSubmission.id == HomeworkSubmissionFeedback.homework_submission_id,
            )
            .join(
                HomeworkAssignment,
                HomeworkAssignment.id == HomeworkSubmission.assignment_id,
            )
            .where(
                HomeworkAssignment.teacher_id == teacher_id,
                HomeworkSubmissionFeedback.teacher_voice_id == audio_id,
            )
            .limit(1)
        )
        return await self._session.scalar(sub_stmt) is not None

    async def student_can_view_audio(
        self,
        student_id: uuid.UUID,
        audio_id: uuid.UUID,
    ) -> bool:
        step_stmt = (
            select(TestSessionStepFeedback.id)
            .join(
                TestSessionStep,
                TestSessionStep.id == TestSessionStepFeedback.test_session_step_id,
            )
            .join(TestSession, TestSession.id == TestSessionStep.session_id)
            .join(
                HomeworkAssignment,
                HomeworkAssignment.id == TestSession.homework_assignment_id,
            )
            .where(
                HomeworkAssignment.student_id == student_id,
                TestSessionStepFeedback.teacher_voice_id == audio_id,
                TestSessionStepFeedback.published_at.is_not(None),
            )
            .limit(1)
        )
        if await self._session.scalar(step_stmt) is not None:
            return True

        sub_stmt = (
            select(HomeworkSubmissionFeedback.id)
            .join(
                HomeworkSubmission,
                HomeworkSubmission.id == HomeworkSubmissionFeedback.homework_submission_id,
            )
            .join(
                HomeworkAssignment,
                HomeworkAssignment.id == HomeworkSubmission.assignment_id,
            )
            .where(
                HomeworkAssignment.student_id == student_id,
                HomeworkSubmissionFeedback.teacher_voice_id == audio_id,
                HomeworkSubmissionFeedback.published_at.is_not(None),
            )
            .limit(1)
        )
        return await self._session.scalar(sub_stmt) is not None
