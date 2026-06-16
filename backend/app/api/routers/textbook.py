"""Textbook endpoints (student-only).

| Method | Path                                              | Role    | Response              |
|--------|---------------------------------------------------|---------|-----------------------|
| GET    | /api/textbook/topics                              | student | list[TopicRead]       |
| GET    | /api/textbook/topics/{topic}/chunks             | student | list[ChunkSummaryRead]|
| GET    | /api/textbook/topics/{topic}/chunks/{idx}         | student | ChunkRead             |
| GET    | /api/textbook/topics/{topic}/chunks/{idx}/audio   | student | audio/ogg stream      |
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import StudentUser, get_app_settings
from app.core.config import Settings
from app.repositories.content.lectures import LectureContentRepo
from app.schemas.textbook import ChunkRead, ChunkSummaryRead, TopicRead
from app.services.textbook_service import TextbookService

router = APIRouter(prefix="/api/textbook", tags=["textbook"])

_AUDIO_CHUNK_SIZE = 64 * 1024


def get_lecture_repo(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> LectureContentRepo:
    return LectureContentRepo(settings.content_lectures_db_path)


def get_textbook_service(
    repo: Annotated[LectureContentRepo, Depends(get_lecture_repo)],
) -> TextbookService:
    return TextbookService(repo)


@router.get("/topics", response_model=list[TopicRead])
def list_topics(
    _student: StudentUser,
    service: Annotated[TextbookService, Depends(get_textbook_service)],
) -> list[TopicRead]:
    return service.list_topics()


@router.get("/topics/{topic}/chunks", response_model=list[ChunkSummaryRead])
def list_chunks(
    topic: str,
    _student: StudentUser,
    service: Annotated[TextbookService, Depends(get_textbook_service)],
) -> list[ChunkSummaryRead]:
    return service.list_chunks(topic)


@router.get("/topics/{topic}/chunks/{chunk_idx}", response_model=ChunkRead)
def get_chunk(
    topic: str,
    chunk_idx: int,
    _student: StudentUser,
    service: Annotated[TextbookService, Depends(get_textbook_service)],
) -> ChunkRead:
    return service.get_chunk(topic, chunk_idx)


def _iter_bytes(data: bytes, chunk_size: int = _AUDIO_CHUNK_SIZE) -> Iterator[bytes]:
    for offset in range(0, len(data), chunk_size):
        yield data[offset : offset + chunk_size]


@router.get("/topics/{topic}/chunks/{chunk_idx}/audio")
def stream_audio(
    topic: str,
    chunk_idx: int,
    _student: StudentUser,
    service: Annotated[TextbookService, Depends(get_textbook_service)],
) -> StreamingResponse:
    audio = service.get_audio(topic, chunk_idx)
    return StreamingResponse(
        _iter_bytes(audio),
        media_type="audio/ogg",
        headers={"Cache-Control": "public, max-age=86400"},
    )
