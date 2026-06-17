"""Data access for homework assignments and submissions (app DB)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import HomeworkAssignment, HomeworkSubmission, HomeworkStatus


class HomeworkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, assignment: HomeworkAssignment) -> HomeworkAssignment:
        self._session.add(assignment)
        await self._session.flush()
        return assignment

    async def get_by_id(self, assignment_id: uuid.UUID) -> HomeworkAssignment | None:
        stmt = (
            select(HomeworkAssignment)
            .where(HomeworkAssignment.id == assignment_id)
            .options(
                joinedload(HomeworkAssignment.student),
                joinedload(HomeworkAssignment.submission),
                selectinload(HomeworkAssignment.item_progress),
            )
        )
        return await self._session.scalar(stmt)

    async def list_by_teacher(self, teacher_id: uuid.UUID) -> list[HomeworkAssignment]:
        stmt = (
            select(HomeworkAssignment)
            .where(HomeworkAssignment.teacher_id == teacher_id)
            .options(
                joinedload(HomeworkAssignment.student),
                joinedload(HomeworkAssignment.submission),
                selectinload(HomeworkAssignment.item_progress),
            )
            .order_by(HomeworkAssignment.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result.unique().all())

    async def list_by_student(self, student_id: uuid.UUID) -> list[HomeworkAssignment]:
        stmt = (
            select(HomeworkAssignment)
            .where(HomeworkAssignment.student_id == student_id)
            .options(
                joinedload(HomeworkAssignment.submission),
                selectinload(HomeworkAssignment.item_progress),
            )
            .order_by(HomeworkAssignment.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result.unique().all())

    async def add_submission(
        self, submission: HomeworkSubmission
    ) -> HomeworkSubmission:
        self._session.add(submission)
        await self._session.flush()
        return submission

    async def get_submission(
        self, assignment_id: uuid.UUID
    ) -> HomeworkSubmission | None:
        return await self._session.scalar(
            select(HomeworkSubmission).where(
                HomeworkSubmission.assignment_id == assignment_id
            )
        )

    async def update_status(
        self, assignment: HomeworkAssignment, status: HomeworkStatus
    ) -> None:
        assignment.status = status
        await self._session.flush()
