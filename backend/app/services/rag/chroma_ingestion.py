"""Chroma ingestion for lecture theory (ported from RAG_chemistry)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator

from langchain_core.documents import Document

from app.core.config import Settings, get_settings
from app.repositories.content.base import open_readonly
from app.services.rag.vectorstore import get_lectures_store


def _iter_lecture_rows(db_path: Path) -> Iterator[sqlite3.Row]:
    with open_readonly(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT topic, chunk_idx, lecture, chunk_title
            FROM prepared_lectures
            ORDER BY topic, chunk_idx
            """
        )
        yield from cursor


def build_chroma_documents(db_path: Path) -> tuple[list[Document], list[str]]:
    documents: list[Document] = []
    ids: list[str] = []

    for row in _iter_lecture_rows(db_path):
        content = (row["lecture"] or "").strip()
        if not content:
            continue
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": "lecture",
                    "topic": row["topic"],
                    "chunk_idx": row["chunk_idx"],
                    "chunk_title": row["chunk_title"] or "",
                },
            )
        )
        ids.append(f'{row["topic"]}::{row["chunk_idx"]}')

    return documents, ids


def ingest_lectures_to_chroma(
    settings: Settings | None = None,
    *,
    rebuild: bool = True,
) -> int:
    """Index lecture chunks into Chroma. Requires OPENAI_API_KEY."""
    app_settings = settings or get_settings()
    store = get_lectures_store()

    if rebuild:
        existing = store.get()
        existing_ids = existing.get("ids") if existing else None
        if existing_ids:
            store.delete(ids=existing_ids)

    documents, ids = build_chroma_documents(app_settings.content_lectures_db_path)
    if not documents:
        return 0

    store.add_documents(documents=documents, ids=ids)
    return len(documents)
