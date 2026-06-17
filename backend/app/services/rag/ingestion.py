"""Build RAG documents from read-only content SQLite databases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.repositories.content.base import open_readonly
from app.services.rag.documents import RagDocument, RagSource


def _parse_qa_pairs(
    qa_questions: str | None,
    qa_answers: str | None,
) -> list[tuple[str, str]]:
    if not qa_questions or not qa_answers:
        return []
    try:
        questions = json.loads(qa_questions)
        answers = json.loads(qa_answers)
    except json.JSONDecodeError:
        return []
    if not isinstance(questions, list) or not isinstance(answers, list):
        return []
    pairs: list[tuple[str, str]] = []
    for question, answer in zip(questions, answers, strict=False):
        if (
            isinstance(question, str)
            and isinstance(answer, str)
            and question.strip()
            and answer.strip()
        ):
            pairs.append((question.strip(), answer.strip()))
    return pairs


def _lecture_doc_id(topic: str, chunk_idx: int) -> str:
    return f"lecture:{topic}:{chunk_idx}"


def _lecture_qa_doc_id(topic: str, chunk_idx: int, qa_idx: int) -> str:
    return f"lecture_qa:{topic}:{chunk_idx}:{qa_idx}"


def _meta(
    *,
    source: RagSource,
    **extra: Any,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {"source": source}
    metadata.update(extra)
    return metadata


def ingest_lecture_documents(lectures_db_path: Path) -> list[RagDocument]:
    """Index lecture chunks and QA pairs. Lectures are track-agnostic."""
    documents: list[RagDocument] = []
    with open_readonly(lectures_db_path) as conn:
        rows = conn.execute(
            """
            SELECT topic, chunk_idx, chunk_title, lecture, qa_questions, qa_answers
            FROM prepared_lectures
            ORDER BY topic, chunk_idx
            """
        ).fetchall()

    for row in rows:
        topic = row["topic"]
        chunk_idx = int(row["chunk_idx"])
        chunk_title = row["chunk_title"] or ""
        lecture = row["lecture"] or ""
        if lecture.strip():
            documents.append(
                RagDocument(
                    doc_id=_lecture_doc_id(topic, chunk_idx),
                    title=f"{topic} — {chunk_title}".strip(" —"),
                    body=lecture.strip(),
                    metadata=_meta(
                        source="lecture",
                        topic=topic,
                        chunk_idx=chunk_idx,
                        chunk_title=chunk_title,
                    ),
                )
            )

        for qa_idx, (question, answer) in enumerate(
            _parse_qa_pairs(row["qa_questions"], row["qa_answers"])
        ):
            documents.append(
                RagDocument(
                    doc_id=_lecture_qa_doc_id(topic, chunk_idx, qa_idx),
                    title=f"{topic} — {chunk_title} (вопрос)".strip(" —"),
                    body=f"Вопрос: {question}\nОтвет: {answer}",
                    metadata=_meta(
                        source="lecture_qa",
                        topic=topic,
                        chunk_idx=chunk_idx,
                        chunk_title=chunk_title,
                        field="question",
                    ),
                )
            )

    return documents


def ingest_all_documents(settings: Settings) -> list[RagDocument]:
    """Collect RAG documents from prepared_lectures (lecture + lecture_qa only)."""
    return ingest_lecture_documents(settings.content_lectures_db_path)


def ingest_all_documents_from_paths(
    *,
    lectures_db_path: Path,
) -> list[RagDocument]:
    """Test helper: ingest lectures without loading full Settings."""
    return ingest_lecture_documents(lectures_db_path)
