"""Textbook API response schemas (read-only content from prepared_lectures.db)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TopicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    topic: str
    chunk_count: int


class ChunkSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_idx: int
    chunk_title: str
    has_audio: bool


class ChunkRead(ChunkSummaryRead):
    topic: str
    lecture: str
