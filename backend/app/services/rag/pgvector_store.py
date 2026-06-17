"""pgvector-backed embedding store + in-memory fallback for tests (Task 41.2)."""

from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import Settings, get_settings
from app.services.rag.documents import ExamTrack, RagChunkHit, RagDocument, RagSource

logger = logging.getLogger(__name__)

TrackFilter = ExamTrack | None
SourceFilter = RagSource | None

_EMBEDDING_DIM = 1536


@dataclass(frozen=True, slots=True)
class VectorRecord:
    doc_id: str
    source: str
    title: str
    body: str
    metadata: dict[str, Any]
    embedding: list[float]


class VectorStore(Protocol):
    def count(self) -> int: ...

    def upsert_batch(self, records: list[VectorRecord]) -> int: ...

    def search(
        self,
        query_embedding: list[float],
        *,
        track: TrackFilter = None,
        source: SourceFilter = None,
        topic: str | None = None,
        limit: int = 10,
    ) -> list[RagChunkHit]: ...


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def _matches_filters(
    metadata: dict[str, Any],
    *,
    track: TrackFilter,
    source: SourceFilter,
    topic: str | None,
) -> bool:
    if source is not None and metadata.get("source") != source:
        return False
    if topic is not None and metadata.get("topic") != topic:
        return False
    if track is not None:
        doc_track = metadata.get("track")
        if doc_track is not None and doc_track != track:
            return False
    return True


def _record_to_metadata(document: RagDocument) -> dict[str, Any]:
    metadata = dict(document.metadata)
    metadata["title"] = document.title
    metadata["body"] = document.body
    return metadata


def _hit_from_record(record: VectorRecord, score: float) -> RagChunkHit:
    return RagChunkHit(
        doc_id=record.doc_id,
        score=score,
        title=record.title,
        body=record.body,
        metadata=dict(record.metadata),
    )


class InMemoryVectorStore:
    """Deterministic cosine search for pytest (no PostgreSQL/pgvector)."""

    def __init__(self) -> None:
        self._records: list[VectorRecord] = []

    def count(self) -> int:
        return len(self._records)

    def upsert_batch(self, records: list[VectorRecord]) -> int:
        by_id = {record.doc_id: record for record in self._records}
        for record in records:
            by_id[record.doc_id] = record
        self._records = list(by_id.values())
        return len(records)

    def search(
        self,
        query_embedding: list[float],
        *,
        track: TrackFilter = None,
        source: SourceFilter = None,
        topic: str | None = None,
        limit: int = 10,
    ) -> list[RagChunkHit]:
        scored: list[RagChunkHit] = []
        for record in self._records:
            if not _matches_filters(
                record.metadata, track=track, source=source, topic=topic
            ):
                continue
            score = _cosine_similarity(query_embedding, record.embedding)
            if score > 0:
                scored.append(_hit_from_record(record, score))
        scored.sort(key=lambda hit: hit.score, reverse=True)
        return scored[:limit]


class PgVectorStore:
    """Async pgvector store with a sync facade for the keyword Retriever."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> PgVectorStore:
        app_settings = settings or get_settings()
        if not app_settings.database_url.startswith("postgresql"):
            raise RuntimeError("pgvector store requires a PostgreSQL DATABASE_URL")
        engine = create_async_engine(app_settings.database_url, echo=False)
        return cls(engine)

    def count(self) -> int:
        return asyncio.run(self._count_async())

    def upsert_batch(self, records: list[VectorRecord]) -> int:
        return asyncio.run(self._upsert_batch_async(records))

    def search(
        self,
        query_embedding: list[float],
        *,
        track: TrackFilter = None,
        source: SourceFilter = None,
        topic: str | None = None,
        limit: int = 10,
    ) -> list[RagChunkHit]:
        return asyncio.run(
            self._search_async(
                query_embedding,
                track=track,
                source=source,
                topic=topic,
                limit=limit,
            )
        )

    async def dispose(self) -> None:
        await self._engine.dispose()

    async def _count_async(self) -> int:
        async with self._engine.connect() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM rag_embeddings"))
            return int(result.scalar_one())

    async def _upsert_batch_async(self, records: list[VectorRecord]) -> int:
        if not records:
            return 0
        async with self._engine.begin() as conn:
            for record in records:
                await conn.execute(
                    text(
                        """
                        INSERT INTO rag_embeddings
                            (doc_id, source, metadata, embedding)
                        VALUES
                            (:doc_id, :source, CAST(:metadata AS jsonb), CAST(:embedding AS vector))
                        ON CONFLICT (doc_id) DO UPDATE SET
                            source = EXCLUDED.source,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding
                        """
                    ),
                    {
                        "doc_id": record.doc_id,
                        "source": record.source,
                        "metadata": _json_dumps(record.metadata),
                        "embedding": _vector_literal(record.embedding),
                    },
                )
        return len(records)

    async def _search_async(
        self,
        query_embedding: list[float],
        *,
        track: TrackFilter,
        source: SourceFilter,
        topic: str | None,
        limit: int,
    ) -> list[RagChunkHit]:
        if limit <= 0:
            return []

        clauses = ["1=1"]
        params: dict[str, Any] = {
            "query_vec": _vector_literal(query_embedding),
            "limit": limit,
        }
        if source is not None:
            clauses.append("source = :source")
            params["source"] = source
        if topic is not None:
            clauses.append("metadata->>'topic' = :topic")
            params["topic"] = topic
        if track is not None:
            clauses.append(
                "(metadata->>'track' IS NULL OR metadata->>'track' = :track)"
            )
            params["track"] = track

        where_sql = " AND ".join(clauses)
        sql = f"""
            SELECT doc_id, source, metadata,
                   1 - (embedding <=> CAST(:query_vec AS vector)) AS score
            FROM rag_embeddings
            WHERE {where_sql}
            ORDER BY embedding <=> CAST(:query_vec AS vector)
            LIMIT :limit
        """
        async with self._engine.connect() as conn:
            result = await conn.execute(text(sql), params)
            rows = result.mappings().all()

        hits: list[RagChunkHit] = []
        for row in rows:
            metadata = dict(row["metadata"] or {})
            title = str(metadata.pop("title", ""))
            body = str(metadata.pop("body", ""))
            hits.append(
                RagChunkHit(
                    doc_id=str(row["doc_id"]),
                    score=float(row["score"] or 0.0),
                    title=title,
                    body=body,
                    metadata=metadata,
                )
            )
        return hits


def build_vector_records(
    documents: list[RagDocument],
    embeddings: list[list[float]],
) -> list[VectorRecord]:
    records: list[VectorRecord] = []
    for document, embedding in zip(documents, embeddings, strict=True):
        source = str(document.metadata.get("source", "lecture"))
        records.append(
            VectorRecord(
                doc_id=document.doc_id,
                source=source,
                title=document.title,
                body=document.body,
                metadata=_record_to_metadata(document),
                embedding=embedding,
            )
        )
    return records


def index_documents_to_store(
    store: VectorStore,
    documents: list[RagDocument],
    *,
    embed_texts: list[str],
    embeddings_provider,
    batch_size: int = 32,
) -> int:
    """Embed and upsert documents in batches."""
    total = 0
    for start in range(0, len(documents), batch_size):
        batch_docs = documents[start : start + batch_size]
        batch_texts = embed_texts[start : start + batch_size]
        vectors = embeddings_provider.embed_documents(batch_texts)
        records = build_vector_records(batch_docs, vectors)
        total += store.upsert_batch(records)
    return total


def _json_dumps(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False)


def _vector_literal(values: list[float]) -> str:
    padded = list(values[:_EMBEDDING_DIM])
    if len(padded) < _EMBEDDING_DIM:
        padded.extend([0.0] * (_EMBEDDING_DIM - len(padded)))
    inner = ",".join(f"{value:.8f}" for value in padded)
    return f"[{inner}]"
