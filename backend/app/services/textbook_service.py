"""Textbook business logic — topics, chunks, audio from content DB."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.repositories.content.base import ContentDbError
from app.repositories.content.lectures import LectureContentRepo
from app.schemas.textbook import ChunkRead, ChunkSummaryRead, TopicRead


class TextbookService:
    def __init__(self, repo: LectureContentRepo) -> None:
        self._repo = repo

    def list_topics(self) -> list[TopicRead]:
        try:
            topics = self._repo.list_topics()
        except ContentDbError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Lecture content database unavailable",
            ) from exc
        return [TopicRead.model_validate(topic) for topic in topics]

    def list_chunks(self, topic: str) -> list[ChunkSummaryRead]:
        try:
            chunks = self._repo.list_chunk_summaries(topic)
        except ContentDbError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Lecture content database unavailable",
            ) from exc
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found",
            )
        return [ChunkSummaryRead.model_validate(chunk) for chunk in chunks]

    def get_chunk(self, topic: str, chunk_idx: int) -> ChunkRead:
        try:
            chunk = self._repo.get_chunk(topic, chunk_idx)
        except ContentDbError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Lecture content database unavailable",
            ) from exc
        if chunk is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chunk not found",
            )
        return ChunkRead.model_validate(chunk)

    def get_audio(self, topic: str, chunk_idx: int) -> bytes:
        try:
            audio = self._repo.get_audio(topic, chunk_idx)
        except ContentDbError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Lecture content database unavailable",
            ) from exc
        if audio is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio not found",
            )
        return audio
