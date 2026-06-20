"""Data access for homework teacher feedback (SPEC §1.9.9)."""

from __future__ import annotations

import uuid

from sqlalchemy import cast, or_, select, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import (
    HomeworkAssignment,
    HomeworkSubmission,
    HomeworkSubmissionFeedback,
    HomeworkStatus,
    TestSession,
    TestSessionStep,
    TestSessionStepFeedback,
)


class HomeworkFeedbackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_step_feedback(
        self,
        test_session_step_id: uuid.UUID,
    ) -> TestSessionStepFeedback | None:
        return await self._session.scalar(
            select(TestSessionStepFeedback).where(
                TestSessionStepFeedback.test_session_step_id == test_session_step_id
            )
        )

    async def get_submission_feedback(
        self,
        homework_submission_id: uuid.UUID,
    ) -> HomeworkSubmissionFeedback | None:
        return await self._session.scalar(
            select(HomeworkSubmissionFeedback).where(
                HomeworkSubmissionFeedback.homework_submission_id
                == homework_submission_id
            )
        )

    async def upsert_step_feedback(
        self,
        *,
        test_session_step_id: uuid.UUID,
        teacher_text: str | None,
        teacher_voice_id: uuid.UUID | None,
        teacher_image_ids: list[str],
        published_at,
    ) -> TestSessionStepFeedback:
        existing = await self.get_step_feedback(test_session_step_id)
        if existing is None:
            row = TestSessionStepFeedback(
                test_session_step_id=test_session_step_id,
                teacher_text=teacher_text,
                teacher_voice_id=teacher_voice_id,
                teacher_image_ids=teacher_image_ids,
                published_at=published_at,
            )
            self._session.add(row)
            await self._session.flush()
            return row

        existing.teacher_text = teacher_text
        existing.teacher_voice_id = teacher_voice_id
        existing.teacher_image_ids = teacher_image_ids
        if existing.published_at is None:
            existing.published_at = published_at
        await self._session.flush()
        return existing

    async def upsert_submission_feedback(
        self,
        *,
        homework_submission_id: uuid.UUID,
        teacher_text: str | None,
        teacher_voice_id: uuid.UUID | None,
        teacher_image_ids: list[str],
        published_at,
    ) -> HomeworkSubmissionFeedback:
        existing = await self.get_submission_feedback(homework_submission_id)
        if existing is None:
            row = HomeworkSubmissionFeedback(
                homework_submission_id=homework_submission_id,
                teacher_text=teacher_text,
                teacher_voice_id=teacher_voice_id,
                teacher_image_ids=teacher_image_ids,
                published_at=published_at,
            )
            self._session.add(row)
            await self._session.flush()
            return row

        existing.teacher_text = teacher_text
        existing.teacher_voice_id = teacher_voice_id
        existing.teacher_image_ids = teacher_image_ids
        if existing.published_at is None:
            existing.published_at = published_at
        await self._session.flush()
        return existing

    async def list_step_feedbacks_for_assignment(
        self,
        assignment_id: uuid.UUID,
    ) -> list[tuple[TestSessionStep, TestSessionStepFeedback | None]]:
        stmt = (
            select(TestSessionStep, TestSessionStepFeedback)
            .join(TestSession, TestSession.id == TestSessionStep.session_id)
            .join(HomeworkSubmission, HomeworkSubmission.test_session_id == TestSession.id)
            .outerjoin(
                TestSessionStepFeedback,
                TestSessionStepFeedback.test_session_step_id == TestSessionStep.id,
            )
            .where(HomeworkSubmission.assignment_id == assignment_id)
            .order_by(TestSessionStep.position)
        )
        rows = await self._session.execute(stmt)
        return list(rows.all())

    async def get_step_for_assignment_position(
        self,
        assignment_id: uuid.UUID,
        position: int,
    ) -> TestSessionStep | None:
        stmt = (
            select(TestSessionStep)
            .join(TestSession, TestSession.id == TestSessionStep.session_id)
            .join(HomeworkSubmission, HomeworkSubmission.test_session_id == TestSession.id)
            .where(
                HomeworkSubmission.assignment_id == assignment_id,
                TestSessionStep.position == position,
            )
        )
        return await self._session.scalar(stmt)

    async def assignment_has_teacher_feedback(
        self,
        assignment_id: uuid.UUID,
    ) -> bool:
        step_image_match = cast(
            TestSessionStepFeedback.teacher_image_ids,
            String,
        ).like('%"')

        step_stmt = (
            select(TestSessionStepFeedback.id)
            .join(
                TestSessionStep,
                TestSessionStep.id == TestSessionStepFeedback.test_session_step_id,
            )
            .join(TestSession, TestSession.id == TestSessionStep.session_id)
            .join(HomeworkSubmission, HomeworkSubmission.test_session_id == TestSession.id)
            .where(
                HomeworkSubmission.assignment_id == assignment_id,
                TestSessionStepFeedback.published_at.is_not(None),
                or_(
                    TestSessionStepFeedback.teacher_text.is_not(None),
                    TestSessionStepFeedback.teacher_voice_id.is_not(None),
                    step_image_match,
                ),
            )
            .limit(1)
        )
        if await self._session.scalar(step_stmt) is not None:
            return True

        sub_image_match = cast(
            HomeworkSubmissionFeedback.teacher_image_ids,
            String,
        ).like('%"')

        sub_stmt = (
            select(HomeworkSubmissionFeedback.id)
            .join(
                HomeworkSubmission,
                HomeworkSubmission.id == HomeworkSubmissionFeedback.homework_submission_id,
            )
            .where(
                HomeworkSubmission.assignment_id == assignment_id,
                HomeworkSubmissionFeedback.published_at.is_not(None),
                or_(
                    HomeworkSubmissionFeedback.teacher_text.is_not(None),
                    HomeworkSubmissionFeedback.teacher_voice_id.is_not(None),
                    sub_image_match,
                ),
            )
            .limit(1)
        )
        return await self._session.scalar(sub_stmt) is not None

    async def get_submitted_assignment_for_teacher(
        self,
        assignment_id: uuid.UUID,
        teacher_id: uuid.UUID,
    ) -> HomeworkAssignment | None:
        stmt = (
            select(HomeworkAssignment)
            .where(
                HomeworkAssignment.id == assignment_id,
                HomeworkAssignment.teacher_id == teacher_id,
                HomeworkAssignment.status == HomeworkStatus.SUBMITTED,
            )
            .options(
                joinedload(HomeworkAssignment.submission),
            )
        )
        return await self._session.scalar(stmt)

    async def get_submitted_assignment_for_student(
        self,
        assignment_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> HomeworkAssignment | None:
        stmt = (
            select(HomeworkAssignment)
            .where(
                HomeworkAssignment.id == assignment_id,
                HomeworkAssignment.student_id == student_id,
                HomeworkAssignment.status == HomeworkStatus.SUBMITTED,
            )
            .options(
                joinedload(HomeworkAssignment.submission),
            )
        )
        return await self._session.scalar(stmt)
