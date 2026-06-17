"""Build RAG documents from read-only content SQLite databases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.repositories.content.base import open_readonly
from app.services.rag.documents import ExamTrack, RagDocument, RagSource, TestField


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


def _test_doc_id(track: ExamTrack, variant: str, test_type: int, field: TestField) -> str:
    return f"test:{track}:{variant}:{test_type}:{field}"


def _meta(
    *,
    source: RagSource,
    track: ExamTrack | None = None,
    **extra: Any,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {"source": source}
    if track is not None:
        metadata["track"] = track
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


def ingest_test_documents(
    tests_db_path: Path,
    *,
    track: ExamTrack,
) -> list[RagDocument]:
    """Index hint and detailed_explanation fields; skip problematic tests."""
    documents: list[RagDocument] = []
    with open_readonly(tests_db_path) as conn:
        rows = conn.execute(
            """
            SELECT t.filename, t.type, t.hint, t.detailed_explanation
            FROM tests t
            WHERE COALESCE(t.has_issue, 0) = 0
              AND t.filename NOT IN (SELECT filename FROM tests_bug)
            ORDER BY t.filename, t.type
            """
        ).fetchall()

    for row in rows:
        variant = row["filename"]
        test_type = int(row["type"])
        for field_name, value in (
            ("hint", row["hint"]),
            ("detailed_explanation", row["detailed_explanation"]),
        ):
            if not value or not str(value).strip():
                continue
            field: TestField = field_name  # type: ignore[assignment]
            documents.append(
                RagDocument(
                    doc_id=_test_doc_id(track, variant, test_type, field),
                    title=f"{track.upper()} {variant} — задание {test_type} ({field})",
                    body=str(value).strip(),
                    metadata=_meta(
                        source="test",
                        track=track,
                        variant=variant,
                        test_type=test_type,
                        field=field,
                    ),
                )
            )

    return documents


def ingest_all_documents(settings: Settings) -> list[RagDocument]:
    """Collect all RAG documents from configured content databases."""
    documents: list[RagDocument] = []
    documents.extend(ingest_lecture_documents(settings.content_lectures_db_path))
    documents.extend(
        ingest_test_documents(settings.content_ege_db_path, track="ege")
    )
    documents.extend(
        ingest_test_documents(settings.content_oge_db_path, track="oge")
    )
    return documents


def ingest_all_documents_from_paths(
    *,
    lectures_db_path: Path,
    ege_db_path: Path,
    oge_db_path: Path,
) -> list[RagDocument]:
    """Test helper: ingest without loading full Settings."""
    documents: list[RagDocument] = []
    documents.extend(ingest_lecture_documents(lectures_db_path))
    documents.extend(ingest_test_documents(ege_db_path, track="ege"))
    documents.extend(ingest_test_documents(oge_db_path, track="oge"))
    return documents
