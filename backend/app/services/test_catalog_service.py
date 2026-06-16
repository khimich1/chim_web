"""Test catalog business logic — variants and questions by student track."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import ExamTrack, StudentProfile, User
from app.repositories.content.base import ContentDbError
from app.repositories.content.tests import ExamContentRepo
from app.schemas.tests import QuestionRead, VariantRead
from app.services.image_substitution import substitute_image_placeholders


class TestCatalogService:
    def __init__(self, settings: Settings) -> None:
        self._repos = {
            ExamTrack.EGE: ExamContentRepo(settings.content_ege_db_path),
            ExamTrack.OGE: ExamContentRepo(settings.content_oge_db_path),
        }

    async def resolve_track(self, session: AsyncSession, student: User) -> ExamTrack:
        profile = await session.scalar(
            select(StudentProfile).where(StudentProfile.user_id == student.id)
        )
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found",
            )
        return profile.track

    def list_variants(self, track: ExamTrack) -> list[VariantRead]:
        repo = self._repos[track]
        try:
            filenames = repo.list_variants()
        except ContentDbError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Test content database unavailable",
            ) from exc
        return [VariantRead(filename=name) for name in filenames]

    def list_questions(self, track: ExamTrack, filename: str) -> list[QuestionRead]:
        repo = self._repos[track]
        try:
            questions = repo.list_questions(filename)
        except ContentDbError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Test content database unavailable",
            ) from exc
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Variant not found",
            )
        return [
            QuestionRead(
                id=q.id,
                filename=q.filename,
                type=q.type,
                question=substitute_image_placeholders(q.question),
                options=q.options,
            )
            for q in questions
        ]

    def get_image(self, track: ExamTrack, filename: str) -> bytes | None:
        repo = self._repos[track]
        try:
            return repo.get_image(filename)
        except ContentDbError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Test content database unavailable",
            ) from exc
