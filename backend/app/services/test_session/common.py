"""Shared helpers and base dependencies for test session adapters."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import StudentProfile, TestSession, TestSessionStep, User
from app.repositories.app.test_session_repo import TestSessionRepository
from app.repositories.app.upload_repo import UploadedImageRepository
from app.repositories.content.tests import ExamContentRepo, ExamTrack
from app.services.activity_service import ActivityService
from app.services.grading_service import GradingService

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def session_duration_minutes(created_at: datetime, completed_at: datetime) -> int:
    seconds = (ensure_utc(completed_at) - ensure_utc(created_at)).total_seconds()
    if seconds <= 0:
        return 0
    return int(seconds // 60)


def answer_image_url(image_id: uuid.UUID | None) -> str | None:
    if image_id is None:
        return None
    return f"/api/uploads/images/{image_id}"


class SessionAdapterBase:
    """Shared DB session, repos, and track resolution for session adapters."""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        activity: ActivityService | None = None,
    ) -> None:
        self._session = session
        self._settings = settings
        self._repo = TestSessionRepository(session)
        self._upload_repo = UploadedImageRepository(session)
        self._grading = GradingService()
        self._activity = activity or ActivityService(session)
        self._content_repos = {
            ExamTrack.EGE: ExamContentRepo(settings.content_ege_db_path),
            ExamTrack.OGE: ExamContentRepo(settings.content_oge_db_path),
        }

    async def run_activity_hook(
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

    async def resolve_track(self, student: User) -> ExamTrack:
        profile = await self._session.scalar(
            select(StudentProfile).where(StudentProfile.user_id == student.id)
        )
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found",
            )
        return profile.track

    def content_repo(self, track: ExamTrack) -> ExamContentRepo:
        return self._content_repos[track]

    async def load_owned_session(
        self, student: User, session_id: uuid.UUID
    ) -> TestSession:
        test_session = await self._repo.get_with_steps(session_id)
        if test_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        if test_session.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your session",
            )
        return test_session

    @staticmethod
    def find_step(test_session: TestSession, position: int) -> TestSessionStep:
        for step in test_session.steps:
            if step.position == position:
                return step
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )
