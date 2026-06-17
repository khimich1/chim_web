"""Search the offline RAG index (keyword + optional hybrid pgvector, Task 41.2)."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from app.core.config import Settings, get_settings
from app.services.rag.documents import ExamTrack, RagChunkHit, RagDocument
from app.services.rag.embeddings import EmbeddingsProvider, get_embeddings_provider
from app.services.rag.ingestion import ingest_all_documents
from app.services.rag.keyword import keyword_score, tokenize
from app.services.rag.pgvector_store import VectorStore
from app.services.rag.rerank import hybrid_rerank
from app.services.rag.store import load_index, save_index

logger = logging.getLogger(__name__)

TrackFilter = ExamTrack | None
SourceFilter = str | None

_HYBRID_POOL_SIZE = 10


class Retriever:
    """Keyword retriever with optional hybrid pgvector rerank."""

    def __init__(
        self,
        documents: list[RagDocument],
        *,
        settings: Settings | None = None,
        vector_store: VectorStore | None = None,
        embeddings_provider: EmbeddingsProvider | None = None,
    ) -> None:
        self._documents = list(documents)
        self._settings = settings
        self._vector_store = vector_store
        self._embeddings_provider = embeddings_provider

    @property
    def document_count(self) -> int:
        return len(self._documents)

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> Retriever:
        app_settings = settings or get_settings()
        if app_settings.rag_index_path.is_file():
            return cls(load_index(app_settings.rag_index_path), settings=app_settings)
        return cls(ingest_all_documents(app_settings), settings=app_settings)

    @classmethod
    def from_index_path(cls, path: Path) -> Retriever:
        return cls(load_index(path))

    def rebuild_index(self, settings: Settings | None = None) -> int:
        """Ingest content DBs and persist the index file."""
        app_settings = settings or get_settings()
        documents = ingest_all_documents(app_settings)
        save_index(documents, app_settings.rag_index_path)
        self._documents = documents
        return len(documents)

    def search(
        self,
        query: str,
        *,
        track: TrackFilter = None,
        source: SourceFilter = None,
        topic: str | None = None,
        limit: int = 4,
    ) -> list[RagChunkHit]:
        if not tokenize(query):
            return []

        settings = self._settings or get_settings()
        if self._should_use_hybrid(settings):
            return self._hybrid_search(
                query,
                track=track,
                source=source,
                topic=topic,
                limit=limit,
                settings=settings,
            )
        return self._keyword_search(
            query,
            track=track,
            source=source,
            topic=topic,
            limit=limit,
        )

    def _should_use_hybrid(self, settings: Settings) -> bool:
        if not settings.rag_hybrid_enabled:
            return False
        store = self._resolve_vector_store(settings)
        if store is None or store.count() == 0:
            return False
        return self._resolve_embeddings_provider(settings) is not None

    def _hybrid_search(
        self,
        query: str,
        *,
        track: TrackFilter,
        source: SourceFilter,
        topic: str | None,
        limit: int,
        settings: Settings,
    ) -> list[RagChunkHit]:
        started = time.perf_counter()
        keyword_hits = self._keyword_search(
            query,
            track=track,
            source=source,
            topic=topic,
            limit=_HYBRID_POOL_SIZE,
        )
        provider = self._resolve_embeddings_provider(settings)
        store = self._resolve_vector_store(settings)
        if provider is None or store is None:
            return keyword_hits[:limit]

        query_vector = provider.embed_query(query)
        vector_hits = store.search(
            query_vector,
            track=track,
            source=source if source in {"lecture", "lecture_qa", "test"} else None,
            topic=topic,
            limit=_HYBRID_POOL_SIZE,
        )
        merged = hybrid_rerank(
            keyword_hits,
            vector_hits,
            pool_size=_HYBRID_POOL_SIZE,
            limit=limit,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "rag.search hybrid query_len=%d keyword_hits=%d vector_hits=%d "
            "returned=%d latency_ms=%.1f",
            len(query),
            len(keyword_hits),
            len(vector_hits),
            len(merged),
            elapsed_ms,
        )
        return merged

    def _keyword_search(
        self,
        query: str,
        *,
        track: TrackFilter,
        source: SourceFilter,
        topic: str | None,
        limit: int,
    ) -> list[RagChunkHit]:
        candidates = [
            document
            for document in self._documents
            if self._matches_filters(document, track=track, source=source, topic=topic)
        ]
        if not candidates:
            return []

        avg_doc_len = self._average_body_length(candidates)
        doc_count = max(len(candidates), 1)

        scored: list[RagChunkHit] = []
        for document in candidates:
            score = keyword_score(
                query,
                title=document.title,
                body=document.body,
                avg_doc_len=avg_doc_len,
                doc_count=doc_count,
            )
            if score > 0:
                scored.append(RagChunkHit.from_document(document, score))

        scored.sort(key=lambda hit: hit.score, reverse=True)
        return scored[:limit]

    def _resolve_vector_store(self, settings: Settings) -> VectorStore | None:
        if self._vector_store is not None:
            return self._vector_store
        if not settings.database_url.startswith("postgresql"):
            return None
        try:
            from app.services.rag.pgvector_store import PgVectorStore

            return PgVectorStore.from_settings(settings)
        except Exception:
            logger.exception("Failed to initialize pgvector store; using keyword-only")
            return None

    def _resolve_embeddings_provider(
        self, settings: Settings
    ) -> EmbeddingsProvider | None:
        if self._embeddings_provider is not None:
            return self._embeddings_provider
        return get_embeddings_provider(settings)

    @staticmethod
    def _matches_filters(
        document: RagDocument,
        *,
        track: TrackFilter,
        source: SourceFilter,
        topic: str | None,
    ) -> bool:
        metadata = document.metadata
        if source is not None and metadata.get("source") != source:
            return False
        if topic is not None and metadata.get("topic") != topic:
            return False
        if track is not None:
            doc_track = metadata.get("track")
            if doc_track is not None and doc_track != track:
                return False
        return True

    @staticmethod
    def _average_body_length(documents: list[RagDocument]) -> float:
        if not documents:
            return 1.0
        total = sum(len(tokenize(document.body)) for document in documents)
        return max(total / len(documents), 1.0)
