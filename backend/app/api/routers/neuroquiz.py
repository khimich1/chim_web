"""Neuroquiz API — student MCQ after textbook chunks.

Gated by Settings.neuroquiz_enabled (NEUROQUIZ_ENABLED). When off, all routes 404.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import StudentUser, get_activity_service, get_app_settings, get_db
from app.core.config import Settings
from app.models.enums import NeuroQuizVoteValue
from app.repositories.content.lectures import LectureContentRepo
from app.schemas.neuroquiz import (
    NeuroQuizAnswerRequest,
    NeuroQuizSession,
    NeuroQuizSubmitResult,
    NeuroQuizVoteRequest,
)
from app.services.activity_service import ActivityService
from app.services.neuroquiz_generate import build_neuroquiz_generator
from app.services.neuroquiz_service import NeuroQuizService

router = APIRouter(prefix="/api/neuroquiz", tags=["neuroquiz"])


def require_neuroquiz_enabled(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> Settings:
    if not settings.neuroquiz_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Neuroquiz is disabled",
        )
    return settings


NeuroQuizEnabled = Annotated[Settings, Depends(require_neuroquiz_enabled)]


def get_neuroquiz_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    activity: Annotated[ActivityService, Depends(get_activity_service)],
) -> NeuroQuizService:
    lectures = LectureContentRepo(settings.content_lectures_db_path)
    return NeuroQuizService(
        db,
        lectures,
        generator=build_neuroquiz_generator(settings),
        activity=activity,
    )


@router.get(
    "/topics/{topic}/chunks/{chunk_idx}",
    response_model=NeuroQuizSession,
)
async def get_neuroquiz_session(
    topic: str,
    chunk_idx: int,
    student: StudentUser,
    _settings: NeuroQuizEnabled,
    service: Annotated[NeuroQuizService, Depends(get_neuroquiz_service)],
) -> NeuroQuizSession:
    return await service.get_session(student, topic, chunk_idx)


@router.post(
    "/topics/{topic}/chunks/{chunk_idx}/warmup",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def warmup_neuroquiz(
    topic: str,
    chunk_idx: int,
    student: StudentUser,
    _settings: NeuroQuizEnabled,
    service: Annotated[NeuroQuizService, Depends(get_neuroquiz_service)],
) -> Response:
    del student  # auth gate; warmup is shared cache
    await service.warmup(topic, chunk_idx)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/topics/{topic}/chunks/{chunk_idx}/answer",
    response_model=NeuroQuizSubmitResult,
)
async def answer_neuroquiz(
    topic: str,
    chunk_idx: int,
    body: NeuroQuizAnswerRequest,
    student: StudentUser,
    _settings: NeuroQuizEnabled,
    service: Annotated[NeuroQuizService, Depends(get_neuroquiz_service)],
) -> NeuroQuizSubmitResult:
    return await service.submit_answer(
        student,
        topic,
        chunk_idx,
        body.question_id,
        body.option_id,
    )


@router.post(
    "/topics/{topic}/chunks/{chunk_idx}/skip",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def skip_neuroquiz(
    topic: str,
    chunk_idx: int,
    student: StudentUser,
    _settings: NeuroQuizEnabled,
    service: Annotated[NeuroQuizService, Depends(get_neuroquiz_service)],
) -> Response:
    await service.skip(student, topic, chunk_idx)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/questions/{question_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
async def vote_neuroquiz(
    question_id: uuid.UUID,
    body: NeuroQuizVoteRequest,
    student: StudentUser,
    _settings: NeuroQuizEnabled,
    service: Annotated[NeuroQuizService, Depends(get_neuroquiz_service)],
) -> Response:
    await service.vote(student, question_id, NeuroQuizVoteValue(body.value))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
