"""Tutor chat API (v2+ AI advisor).

| Method | Path                              | Role            | Description              |
|--------|-----------------------------------|-----------------|--------------------------|
| GET    | /api/tutor/health/tutor           | student/teacher | Tutor readiness check    |
| POST   | /api/tutor/sessions               | student/teacher | Create session           |
| GET    | /api/tutor/sessions               | student/teacher | List own sessions        |
| GET    | /api/tutor/sessions/{id}          | student/teacher | Session + messages       |
| POST   | /api/tutor/sessions/{id}/messages | student/teacher | Send message → agent     |
| GET    | /api/tutor/students/{id}/sessions | teacher         | Student sessions (RBAC)  |
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, TeacherUser, get_app_settings
from app.core.config import Settings
from app.db.session import get_db
from app.schemas.tutor import (
    TutorHealthResponse,
    TutorMessageCreate,
    TutorMessageResponse,
    TutorSessionCreate,
    TutorSessionDetail,
    TutorSessionSummary,
)
from app.services.tutor_service import TutorService

router = APIRouter(prefix="/api/tutor", tags=["tutor"])


@router.get("/health/tutor", response_model=TutorHealthResponse)
def get_tutor_health(
    user: CurrentUser,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> TutorHealthResponse:
    # B4: requires auth — readiness flags (openai_configured / rag_index_exists)
    # are infrastructure details that must not be disclosed to anonymous callers.
    return TutorService.get_health(settings)


def get_tutor_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> TutorService:
    return TutorService(db, settings=settings)


@router.post("/sessions", response_model=TutorSessionSummary, status_code=201)
async def create_tutor_session(
    payload: TutorSessionCreate,
    user: CurrentUser,
    service: Annotated[TutorService, Depends(get_tutor_service)],
) -> TutorSessionSummary:
    return await service.create_session(user, payload)


@router.get("/sessions", response_model=list[TutorSessionSummary])
async def list_tutor_sessions(
    user: CurrentUser,
    service: Annotated[TutorService, Depends(get_tutor_service)],
) -> list[TutorSessionSummary]:
    return await service.list_sessions(user)


@router.get("/sessions/{session_id}", response_model=TutorSessionDetail)
async def get_tutor_session(
    session_id: uuid.UUID,
    user: CurrentUser,
    service: Annotated[TutorService, Depends(get_tutor_service)],
) -> TutorSessionDetail:
    return await service.get_session(user, session_id)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=TutorMessageResponse,
)
async def send_tutor_message(
    session_id: uuid.UUID,
    payload: TutorMessageCreate,
    user: CurrentUser,
    service: Annotated[TutorService, Depends(get_tutor_service)],
) -> TutorMessageResponse:
    return await service.send_message(user, session_id, payload)


@router.get(
    "/students/{student_id}/sessions",
    response_model=list[TutorSessionSummary],
)
async def list_student_tutor_sessions(
    student_id: uuid.UUID,
    teacher: TeacherUser,
    service: Annotated[TutorService, Depends(get_tutor_service)],
) -> list[TutorSessionSummary]:
    return await service.list_student_sessions(teacher, student_id)
