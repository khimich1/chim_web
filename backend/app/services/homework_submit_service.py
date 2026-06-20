"""Homework submission flows for multi-item assignments (SPEC §1.7).

An assignment can mix lecture items and test items drawn from several variants.
Test items are taken together in one aggregated ``TestSession`` (linked by
``homework_assignment_id``); lectures are marked "Прочитано" individually.

``submit`` finalizes the whole assignment: it requires the aggregated test
session (if any test items exist) to be completed, auto-confirms lecture reads,
records an aggregated score, and notifies the teacher once — only at 100%.
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

from app.models import (
    HomeworkAssignment,
    HomeworkStatus,
    HomeworkSubmission,
    Notification,
    NotificationType,
    TestSession,
    TestSessionStatus,
    User,
)
from app.models.enums import HomeworkItemKind
from app.repositories.app.homework_repo import HomeworkRepository
from app.repositories.app.notification_repo import NotificationRepository
from app.repositories.app.test_session_repo import TestSessionRepository
from app.schemas.homework import HomeworkRead, HomeworkSubmitRequest
from app.services.activity_service import ActivityService
from app.services.homework_mapper import to_homework_read

logger = logging.getLogger(__name__)

_T = TypeVar("_T")

_TEST_KINDS = {
    HomeworkItemKind.TEST_VARIANT.value,
    HomeworkItemKind.TEST_PARTIAL.value,
    HomeworkItemKind.TEST_BY_TYPE.value,
    HomeworkItemKind.CUSTOM_THEME.value,
}


class HomeworkSubmitService:
    def __init__(
        self,
        session: AsyncSession,
        activity: ActivityService | None = None,
    ) -> None:
        self._session = session
        self._homework = HomeworkRepository(session)
        self._sessions = TestSessionRepository(session)
        self._notifications = NotificationRepository(session)
        self._activity = activity or ActivityService(session)

    async def _run_activity_hook(
        self,
        hook_name: str,
        action: Callable[[], Awaitable[_T]],
    ) -> None:
        try:
            await action()
            await self._session.commit()
        except Exception:
            logger.exception("Activity hook failed: %s", hook_name)
            await self._session.rollback()

    async def submit(
        self,
        student: User,
        assignment_id: uuid.UUID,
        data: HomeworkSubmitRequest,
    ) -> HomeworkRead:
        assignment = await self._load_owned_assignment(student, assignment_id)
        if await self._homework.get_submission(assignment_id) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Homework already submitted",
            )
        if not assignment.items:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Homework has no items to submit",
            )

        has_test_items = any(
            item.get("kind") in _TEST_KINDS for item in assignment.items
        )

        if not has_test_items and data.test_session_id is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="This homework has no test items; test_session_id is not allowed",
            )

        test_session: TestSession | None = None
        if has_test_items:
            test_session = await self._resolve_completed_test_session(
                student, assignment, data.test_session_id
            )

        now = datetime.now(timezone.utc)
        for progress in assignment.item_progress:
            if not progress.completed:
                progress.completed = True
                progress.completed_at = now

        submission = HomeworkSubmission(
            assignment_id=assignment.id,
            submitted_at=now,
            test_session_id=test_session.id if test_session else None,
            score=test_session.score if test_session else None,
            max_score=test_session.max_score if test_session else None,
        )
        await self._homework.add_submission(submission)
        await self._homework.update_status(assignment, HomeworkStatus.SUBMITTED)
        await self._notify_teacher(assignment, student)
        await self._session.commit()

        assignment_id = assignment.id
        student_id = student.id
        await self._run_activity_hook(
            "record_homework_complete",
            lambda: self._activity.record_homework_complete(student_id, assignment_id),
        )

        self._session.expire_all()

        reloaded = await self._homework.get_by_id(assignment_id)
        assert reloaded is not None
        active_id = await self._active_session_id(student.id, assignment_id)
        return to_homework_read(reloaded, active_test_session_id=active_id)

    async def complete_item(
        self,
        student: User,
        assignment_id: uuid.UUID,
        item_index: int,
    ) -> HomeworkRead:
        """Mark a single lecture item as read ("Прочитано").

        Test items are completed by finishing the aggregated TestSession, not via
        this endpoint.
        """
        assignment = await self._load_owned_assignment(student, assignment_id)
        if assignment.status == HomeworkStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Homework already submitted",
            )
        if not 0 <= item_index < len(assignment.items):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Homework item not found",
            )
        if assignment.items[item_index].get("kind") != HomeworkItemKind.LECTURE.value:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only lecture items can be marked read directly",
            )

        progress = self._progress_for_index(assignment, item_index)
        if not progress.completed:
            progress.completed = True
            progress.completed_at = datetime.now(timezone.utc)
        if assignment.status == HomeworkStatus.ASSIGNED:
            await self._homework.update_status(assignment, HomeworkStatus.IN_PROGRESS)
        await self._session.commit()
        self._session.expire_all()

        reloaded = await self._homework.get_by_id(assignment_id)
        assert reloaded is not None
        active_id = await self._active_session_id(student.id, assignment_id)
        return to_homework_read(reloaded, active_test_session_id=active_id)

    async def mark_in_progress(
        self,
        student: User,
        assignment_id: uuid.UUID,
    ) -> None:
        assignment = await self._load_owned_assignment(student, assignment_id)
        if assignment.status == HomeworkStatus.ASSIGNED:
            await self._homework.update_status(assignment, HomeworkStatus.IN_PROGRESS)
            await self._session.commit()

    async def _active_session_id(
        self,
        student_id: uuid.UUID,
        homework_assignment_id: uuid.UUID,
    ) -> uuid.UUID | None:
        active = await self._sessions.find_latest_active(
            student_id,
            homework_assignment_id=homework_assignment_id,
        )
        return active.id if active is not None else None

    async def _resolve_completed_test_session(
        self,
        student: User,
        assignment: HomeworkAssignment,
        test_session_id: uuid.UUID | None,
    ) -> TestSession:
        if test_session_id is not None:
            test_session = await self._sessions.get_with_steps(test_session_id)
            if test_session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Test session not found",
                )
            if test_session.student_id != student.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not your test session",
                )
            if test_session.homework_assignment_id != assignment.id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Test session is not linked to this homework",
                )
            if test_session.status != TestSessionStatus.COMPLETED:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Complete the test session before submitting homework",
                )
            return test_session

        # No explicit id: use the latest completed session linked to this homework.
        stmt = (
            select(TestSession)
            .where(
                TestSession.homework_assignment_id == assignment.id,
                TestSession.student_id == student.id,
                TestSession.status == TestSessionStatus.COMPLETED,
            )
            .order_by(TestSession.created_at.desc())
        )
        test_session = await self._session.scalar(stmt)
        if test_session is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Complete the test session before submitting homework",
            )
        return test_session

    async def _load_owned_assignment(
        self,
        student: User,
        assignment_id: uuid.UUID,
    ) -> HomeworkAssignment:
        assignment = await self._homework.get_by_id(assignment_id)
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

    @staticmethod
    def _progress_for_index(assignment: HomeworkAssignment, item_index: int):
        for progress in assignment.item_progress:
            if progress.item_index == item_index:
                return progress
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework item progress not found",
        )

    async def _notify_teacher(
        self,
        assignment: HomeworkAssignment,
        student: User,
    ) -> None:
        notification = Notification(
            user_id=assignment.teacher_id,
            type=NotificationType.HOMEWORK_SUBMITTED,
            payload={
                "homework_id": str(assignment.id),
                "homework_title": assignment.title,
                "student_id": str(student.id),
                "student_email": student.email,
            },
        )
        await self._notifications.add(notification)
