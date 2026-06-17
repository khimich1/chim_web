"""Tests catalog endpoints (student-only).

| Method | Path                                      | Role    | Response              |
|--------|-------------------------------------------|---------|-----------------------|
| GET    | /api/tests/variants                       | student | list[VariantRead]     |
| GET    | /api/tests/variants/{filename}/questions  | student | list[QuestionRead]    |
| GET    | /api/tests/images/{filename}              | student | image/png stream      |
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, StudentUser, get_app_settings
from app.core.config import Settings
from app.db.session import get_db
from app.models.enums import ExamTrack, UserRole
from app.schemas.tests import QuestionRead, VariantRead
from app.services.test_catalog_service import TestCatalogService

router = APIRouter(prefix="/api/tests", tags=["tests"])


def get_test_catalog_service(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> TestCatalogService:
    return TestCatalogService(settings)


@router.get("/variants", response_model=list[VariantRead])
async def list_variants(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[TestCatalogService, Depends(get_test_catalog_service)],
    track: ExamTrack | None = Query(
        default=None,
        description="Required when the caller is a teacher",
    ),
) -> list[VariantRead]:
    if user.role == UserRole.TEACHER:
        if track is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="track query parameter is required for teachers",
            )
        resolved_track = track
    else:
        resolved_track = await service.resolve_track(db, user)
    return service.list_variants(resolved_track)


@router.get("/variants/{filename}/questions", response_model=list[QuestionRead])
async def list_questions(
    filename: str,
    student: StudentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[TestCatalogService, Depends(get_test_catalog_service)],
) -> list[QuestionRead]:
    track = await service.resolve_track(db, student)
    return service.list_questions(track, filename)


@router.get("/images/{filename}")
async def get_image(
    filename: str,
    student: StudentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[TestCatalogService, Depends(get_test_catalog_service)],
) -> Response:
    track = await service.resolve_track(db, student)
    data = service.get_image(track, filename)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return Response(content=data, media_type="image/png")
