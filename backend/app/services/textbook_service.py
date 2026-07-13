"""Textbook business logic — topics, chunks, audio from content DB."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, status

from app.repositories.content.base import ContentDbError
from app.repositories.content.lectures import LectureContentRepo
from app.schemas.textbook import ChunkRead, ChunkSummaryRead, TopicRead
from app.schemas.textbook_sections import SectionRead
from app.services.textbook_sections_config import (
    TextbookSectionsConfig,
    TextbookSectionsConfigError,
    get_textbook_sections_config,
)


class TextbookService:
    def __init__(
        self,
        repo: LectureContentRepo,
        sections_config_path: Path,
    ) -> None:
        self._repo = repo
        self._sections_config_path = sections_config_path
        self._sections: TextbookSectionsConfig | None = None

    def _get_sections(self) -> TextbookSectionsConfig:
        if self._sections is not None:
            return self._sections
        try:
            db_topics = {topic.topic for topic in self._repo.list_topics()}
            self._sections = get_textbook_sections_config(
                self._sections_config_path,
                db_topics,
            )
        except ContentDbError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Lecture content database unavailable",
            ) from exc
        except TextbookSectionsConfigError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        return self._sections

    def list_sections(self) -> list[SectionRead]:
        sections = self._get_sections()
        return [
            SectionRead(
                section_id=section_id,
                title=title,
                topic_count=topic_count,
            )
            for section_id, title, topic_count in sections.list_sections()
        ]

    def list_topics(self, section: str | None = None) -> list[TopicRead]:
        if section is not None:
            known_sections = {"basics", "elements", "organic"}
            if section not in known_sections:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Unknown section: {section}",
                )

        try:
            topics = self._repo.list_topics()
        except ContentDbError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Lecture content database unavailable",
            ) from exc

        sections = self._get_sections()
        result: list[TopicRead] = []

        for topic in topics:
            meta = sections.topic_meta(topic.topic)
            if meta is None:
                continue
            if section is not None and meta.section_id != section:
                continue
            result.append(
                TopicRead(
                    topic=topic.topic,
                    chunk_count=topic.chunk_count,
                    section=meta.section_id,
                    video_url=meta.video_url,
                )
            )

        return result

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
