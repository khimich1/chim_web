"""QR handoff token business logic (SPEC §1.9.9, Task 79)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import (
    CustomTask,
    StepStatus,
    TestSession,
    TestSessionStatus,
    TestSessionStep,
    UploadHandoffToken,
    User,
)
from app.models.enums import GradingMode
from app.repositories.app.teacher_theme_repo import TeacherThemeRepository
from app.repositories.app.test_session_repo import TestSessionRepository
from app.repositories.app.upload_handoff_repo import UploadHandoffTokenRepository
from app.repositories.app.upload_repo import UploadedImageRepository
from app.repositories.app.user_repo import UserRepository
from app.schemas.handoff import (
    CaptureMetaResponse,
    CaptureUploadResponse,
    HandoffCreateResponse,
)
from app.services.upload_service import UploadService

_HANDOFF_TTL = timedelta(minutes=15)


def _question_preview(task: CustomTask) -> str | None:
    for block in task.question_blocks or []:
        if isinstance(block, dict) and block.get("type") == "text":
            content = block.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
    return task.title


class UploadHandoffService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
    ) -> None:
        self._session = session
        self._settings = settings
        self._handoff_repo = UploadHandoffTokenRepository(session)
        self._session_repo = TestSessionRepository(session)
        self._theme_repo = TeacherThemeRepository(session)
        self._upload_repo = UploadedImageRepository(session)
        self._user_repo = UserRepository(session)
        self._upload_service = UploadService(self._upload_repo, settings)

    async def create_handoff(
        self,
        student: User,
        session_id: uuid.UUID,
        position: int,
    ) -> HandoffCreateResponse:
        test_session = await self._load_owned_session(student, session_id)
        self._ensure_handoff_allowed(test_session, position)
        step, task = await self._load_step_and_task(test_session, position)
        self._ensure_self_check_homework_step(test_session, step, task)
        if step.status == StepStatus.CHECKED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot create handoff after compare",
            )

        await self._handoff_repo.invalidate_unused_for_step(
            session_id,
            position,
            invalidated_at=datetime.now(timezone.utc),
        )
        expires_at = datetime.now(timezone.utc) + _HANDOFF_TTL
        record = await self._handoff_repo.create(
            session_id=session_id,
            position=position,
            student_id=student.id,
            expires_at=expires_at,
        )
        await self._session.commit()

        capture_url = (
            f"{self._settings.frontend_url.rstrip('/')}"
            f"/student/capture/{record.token}"
        )
        return HandoffCreateResponse(
            token=record.token,
            capture_url=capture_url,
            expires_at=record.expires_at,
        )

    async def get_capture_meta(self, token: uuid.UUID) -> CaptureMetaResponse:
        record = await self._require_active_token(token)
        test_session = await self._load_session(record.session_id)
        step, task = await self._load_step_and_task(test_session, record.position)

        return CaptureMetaResponse(
            session_id=record.session_id,
            position=record.position,
            task_title=task.title,
            question_preview=_question_preview(task),
            expires_at=record.expires_at,
            already_has_photo=step.answer_image_id is not None,
        )

    async def capture_upload(
        self,
        token: uuid.UUID,
        upload: UploadFile,
    ) -> CaptureUploadResponse:
        record = await self._require_active_token(token)
        test_session = await self._load_session(record.session_id)
        step, task = await self._load_step_and_task(test_session, record.position)
        self._ensure_self_check_homework_step(test_session, step, task)
        if step.status == StepStatus.CHECKED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot replace photo after compare",
            )

        student = await self._user_repo.get_by_id(record.student_id)
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        image_response = await self._upload_service.save_image(student, upload)
        step.answer_image_id = image_response.id
        await self._handoff_repo.mark_used(record, datetime.now(timezone.utc))
        await self._session.commit()

        return CaptureUploadResponse(
            position=step.position,
            answer_image_id=image_response.id,
            answer_image_url=image_response.url,
        )

    async def _require_active_token(self, token: uuid.UUID) -> UploadHandoffToken:
        record = await self._handoff_repo.get_by_token(token)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Handoff token not found",
            )
        now = datetime.now(timezone.utc)
        if record.used_at is not None:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Handoff token already used",
            )
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Handoff token expired",
            )
        return record

    async def _load_owned_session(
        self,
        student: User,
        session_id: uuid.UUID,
    ) -> TestSession:
        test_session = await self._session_repo.get_with_steps(session_id)
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

    async def _load_session(self, session_id: uuid.UUID) -> TestSession:
        test_session = await self._session_repo.get_with_steps(session_id)
        if test_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        return test_session

    @staticmethod
    def _ensure_handoff_allowed(test_session: TestSession, position: int) -> None:
        if test_session.status == TestSessionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Session already completed",
            )
        if test_session.homework_assignment_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Handoff is only for homework sessions",
            )
        if position < 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Step not found",
            )

    @staticmethod
    def _ensure_self_check_homework_step(
        test_session: TestSession,
        step: TestSessionStep,
        task: CustomTask,
    ) -> None:
        if test_session.homework_assignment_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Handoff is only for homework sessions",
            )
        if task.grading_mode != GradingMode.SELF_CHECK:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Handoff is only for self_check steps",
            )

    async def _load_step_and_task(
        self,
        test_session: TestSession,
        position: int,
    ) -> tuple[TestSessionStep, CustomTask]:
        step = self._find_step(test_session, position)
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
        return step, task

    @staticmethod
    def _find_step(test_session: TestSession, position: int) -> TestSessionStep:
        for step in test_session.steps:
            if step.position == position:
                return step
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )
