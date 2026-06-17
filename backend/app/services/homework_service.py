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
from app.models.enums import HomeworkItemKind
from app.core.config import get_settings
from app.repositories.app.homework_repo import HomeworkRepository
from app.repositories.app.student_repo import StudentRepository
from app.repositories.app.test_session_repo import TestSessionRepository
from app.schemas.homework import HomeworkCreate, HomeworkRead
from app.services.homework_mapper import to_homework_read
from app.services.homework_validation import validate_homework_items


class HomeworkService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._homework = HomeworkRepository(session)
        self._students = StudentRepository(session)
        self._test_sessions = TestSessionRepository(session)

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

        validate_homework_items(
            data.items,
            track=student.student_profile.track,
            settings=get_settings(),
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
            return [
                to_homework_read(assignment, include_student_email=True)
                for assignment in assignments
            ]
        assignments = await self._homework.list_by_student(user.id)
        result: list[HomeworkRead] = []
        for assignment in assignments:
            active_id = await self._active_session_id(user.id, assignment.id)
            result.append(
                to_homework_read(assignment, active_test_session_id=active_id)
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
            )
        if assignment.student_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your homework assignment",
            )
        active_id = await self._active_session_id(user.id, assignment.id)
        return to_homework_read(assignment, active_test_session_id=active_id)
