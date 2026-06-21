"""PostgreSQL-backed keyword RAG document store (Task 96, Phase 17c)."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Protocol

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import Settings, get_settings
from app.services.rag.documents import RagDocument

logger = logging.getLogger(__name__)


class DocumentStore(Protocol):
    def count(self) -> int: ...

    def load_all(self) -> list[RagDocument]: ...

    def rebuild(self, documents: list[RagDocument]) -> int: ...


class InMemoryDocumentStore:
    """Deterministic document store for pytest (no PostgreSQL)."""

    def __init__(self) -> None:
        self._documents: list[RagDocument] = []

    def count(self) -> int:
        return len(self._documents)

    def load_all(self) -> list[RagDocument]:
        return list(self._documents)

    def rebuild(self, documents: list[RagDocument]) -> int:
        self._documents = list(documents)
        return len(self._documents)


class PgDocumentStore:
    """Async PostgreSQL document store with a sync facade for Retriever."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> PgDocumentStore:
        app_settings = settings or get_settings()
        if not app_settings.database_url.startswith("postgresql"):
            raise RuntimeError("PgDocumentStore requires a PostgreSQL DATABASE_URL")
        engine = create_async_engine(app_settings.database_url, echo=False)
        return cls(engine)

    def count(self) -> int:
        return asyncio.run(self._count_async())

    def load_all(self) -> list[RagDocument]:
        return asyncio.run(self._load_all_async())

    def rebuild(self, documents: list[RagDocument]) -> int:
        return asyncio.run(self._rebuild_async(documents))

    async def dispose(self) -> None:
        await self._engine.dispose()

    async def _count_async(self) -> int:
        async with self._engine.connect() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM rag_documents"))
            return int(result.scalar_one())

    async def _load_all_async(self) -> list[RagDocument]:
        async with self._engine.connect() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT doc_id, title, body, metadata
                    FROM rag_documents
                    ORDER BY doc_id
                    """
                )
            )
            rows = result.mappings().all()

        documents: list[RagDocument] = []
        for row in rows:
            documents.append(_document_from_row(row))
        return documents

    async def _rebuild_async(self, documents: list[RagDocument]) -> int:
        async with self._engine.begin() as conn:
            await conn.execute(text("DELETE FROM rag_documents"))
            for document in documents:
                await conn.execute(
                    text(
                        """
                        INSERT INTO rag_documents
                            (doc_id, source, title, body, metadata)
                        VALUES
                            (:doc_id, :source, :title, :body, CAST(:metadata AS jsonb))
                        """
                    ),
                    {
                        "doc_id": document.doc_id,
                        "source": str(document.metadata.get("source", "lecture")),
                        "title": document.title,
                        "body": document.body,
                        "metadata": _json_dumps(document.metadata),
                    },
                )
        return len(documents)


def load_documents_from_settings(settings: Settings | None = None) -> list[RagDocument]:
    """Load keyword documents from PostgreSQL; returns [] when unavailable."""
    app_settings = settings or get_settings()
    if not app_settings.database_url.startswith("postgresql"):
        return []
    try:
        store = PgDocumentStore.from_settings(app_settings)
        try:
            return store.load_all()
        finally:
            asyncio.run(store.dispose())
    except Exception:
        logger.exception("Failed to load RAG documents from PostgreSQL")
        return []


def rag_documents_ready(settings: Settings | None = None) -> bool:
    """True when PostgreSQL keyword index has at least one document."""
    app_settings = settings or get_settings()
    if not app_settings.database_url.startswith("postgresql"):
        return False
    try:
        store = PgDocumentStore.from_settings(app_settings)
        try:
            return store.count() > 0
        finally:
            asyncio.run(store.dispose())
    except Exception:
        logger.exception("Failed to check RAG document store readiness")
        return False


def _document_from_row(row: dict[str, Any]) -> RagDocument:
    metadata = dict(row["metadata"] or {})
    return RagDocument(
        doc_id=str(row["doc_id"]),
        title=str(row["title"]),
        body=str(row["body"]),
        metadata=metadata,
    )


def _json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)
