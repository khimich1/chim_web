"""Search the offline RAG index (keyword slice 2a)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from app.core.config import Settings, get_settings
from app.services.rag.documents import ExamTrack, RagChunkHit, RagDocument
from app.services.rag.ingestion import ingest_all_documents
from app.services.rag.keyword import keyword_score, tokenize
from app.services.rag.store import load_index, save_index

TrackFilter = ExamTrack | None
SourceFilter = Literal["lecture", "lecture_qa", "test"] | None


class Retriever:
    """Keyword retriever with optional track/source/topic filters."""

    def __init__(self, documents: list[RagDocument]) -> None:
        self._documents = list(documents)

    @property
    def document_count(self) -> int:
        return len(self._documents)

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> Retriever:
        app_settings = settings or get_settings()
        if app_settings.rag_index_path.is_file():
            return cls(load_index(app_settings.rag_index_path))
        return cls(ingest_all_documents(app_settings))

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
