"""Test session endpoints (student-only, Stepik-style flow).

| Method | Path                                          | Role    | Response          |
|--------|-----------------------------------------------|---------|-------------------|
| POST   | /api/tests/sessions                           | student | SessionRead (201) |
| GET    | /api/tests/sessions/active                    | student | ActiveSessionResponse |
| GET    | /api/tests/sessions/{id}                      | student | SessionRead       |
| POST   | /api/tests/sessions/{id}/steps/{n}/check      | student | StepCheckResponse |
| GET    | /api/tests/sessions/{id}/steps/{n}/hint       | student | HintResponse      |
| POST   | /api/tests/sessions/{id}/complete             | student | SessionSummary    |
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import StudentUser, get_app_settings
from app.core.config import Settings
from app.db.session import get_db
from app.schemas.test_session import (
    ActiveSessionResponse,
    HintResponse,
    SessionCreate,
    SessionRead,
    SessionSummary,
    StepCheckRequest,
    StepCheckResponse,
)
from app.services.test_session_service import TestSessionService

router = APIRouter(prefix="/api/tests/sessions", tags=["test-sessions"])


def get_test_session_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> TestSessionService:
    return TestSessionService(db, settings)


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    student: StudentUser,
    service: Annotated[TestSessionService, Depends(get_test_session_service)],
) -> SessionRead:
    return await service.create_session(student, payload)


@router.get("/active", response_model=ActiveSessionResponse)
async def get_active_session(
    student: StudentUser,
    service: Annotated[TestSessionService, Depends(get_test_session_service)],
    variant_ref: str | None = None,
    homework_assignment_id: uuid.UUID | None = None,
) -> ActiveSessionResponse:
    return await service.get_active_session(
        student,
        variant_ref=variant_ref,
        homework_assignment_id=homework_assignment_id,
    )


@router.get("/{session_id}", response_model=SessionRead)
async def get_session(
    session_id: uuid.UUID,
    student: StudentUser,
    service: Annotated[TestSessionService, Depends(get_test_session_service)],
) -> SessionRead:
    return await service.get_session(student, session_id)


@router.post(
    "/{session_id}/steps/{position}/check",
    response_model=StepCheckResponse,
)
async def check_step(
    session_id: uuid.UUID,
    position: int,
    payload: StepCheckRequest,
    student: StudentUser,
    service: Annotated[TestSessionService, Depends(get_test_session_service)],
) -> StepCheckResponse:
    return await service.check_step(student, session_id, position, payload.answer)


@router.get(
    "/{session_id}/steps/{position}/hint",
    response_model=HintResponse,
)
async def get_hint(
    session_id: uuid.UUID,
    position: int,
    student: StudentUser,
    service: Annotated[TestSessionService, Depends(get_test_session_service)],
) -> HintResponse:
    return await service.get_hint(student, session_id, position)


@router.post("/{session_id}/complete", response_model=SessionSummary)
async def complete_session(
    session_id: uuid.UUID,
    student: StudentUser,
    service: Annotated[TestSessionService, Depends(get_test_session_service)],
) -> SessionSummary:
    return await service.complete_session(student, session_id)
