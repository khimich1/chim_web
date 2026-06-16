"""Read-only repository for prepared_lectures.db."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.repositories.content.base import open_readonly


@dataclass(frozen=True, slots=True)
class ChunkSummary:
    chunk_idx: int
    chunk_title: str
    has_audio: bool


@dataclass(frozen=True, slots=True)
class TopicSummary:
    topic: str
    chunk_count: int


@dataclass(frozen=True, slots=True)
class LectureChunk:
    topic: str
    chunk_idx: int
    chunk_title: str
    lecture: str
    has_audio: bool


class LectureContentRepo:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def list_topics(self) -> list[TopicSummary]:
        """Topics ordered by first appearance in DB (ORDER BY MIN(rowid))."""
        with open_readonly(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT topic, COUNT(*) AS chunk_count
                FROM prepared_lectures
                GROUP BY topic
                ORDER BY MIN(rowid)
                """
            ).fetchall()

        return [
            TopicSummary(topic=row["topic"], chunk_count=row["chunk_count"])
            for row in rows
        ]

    def list_chunk_summaries(self, topic: str) -> list[ChunkSummary]:
        with open_readonly(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT chunk_idx, chunk_title, tts_audio
                FROM prepared_lectures
                WHERE topic = ?
                ORDER BY chunk_idx
                """,
                (topic,),
            ).fetchall()

        return [
            ChunkSummary(
                chunk_idx=row["chunk_idx"],
                chunk_title=row["chunk_title"],
                has_audio=row["tts_audio"] is not None,
            )
            for row in rows
        ]

    def get_chunk(self, topic: str, chunk_idx: int) -> LectureChunk | None:
        with open_readonly(self._db_path) as conn:
            row = conn.execute(
                """
                SELECT topic, chunk_idx, chunk_title, lecture, tts_audio
                FROM prepared_lectures
                WHERE topic = ? AND chunk_idx = ?
                """,
                (topic, chunk_idx),
            ).fetchone()

        if row is None:
            return None

        return LectureChunk(
            topic=row["topic"],
            chunk_idx=row["chunk_idx"],
            chunk_title=row["chunk_title"],
            lecture=row["lecture"],
            has_audio=row["tts_audio"] is not None,
        )

    def get_audio(self, topic: str, chunk_idx: int) -> bytes | None:
        with open_readonly(self._db_path) as conn:
            row = conn.execute(
                """
                SELECT tts_audio
                FROM prepared_lectures
                WHERE topic = ? AND chunk_idx = ?
                """,
                (topic, chunk_idx),
            ).fetchone()

        if row is None or row["tts_audio"] is None:
            return None
        return bytes(row["tts_audio"])

    def list_chunks(self, topic: str) -> list[LectureChunk]:
        with open_readonly(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT topic, chunk_idx, chunk_title, lecture, tts_audio
                FROM prepared_lectures
                WHERE topic = ?
                ORDER BY chunk_idx
                """,
                (topic,),
            ).fetchall()

        return [
            LectureChunk(
                topic=row["topic"],
                chunk_idx=row["chunk_idx"],
                chunk_title=row["chunk_title"],
                lecture=row["lecture"],
                has_audio=row["tts_audio"] is not None,
            )
            for row in rows
        ]
