"""RAG document types and metadata (tutor-rag.md §2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

RagSource = Literal["lecture", "lecture_qa", "test"]
ExamTrack = Literal["ege", "oge"]
TestField = Literal["hint", "detailed_explanation", "question", "answer"]


@dataclass(frozen=True, slots=True)
class RagDocument:
    """Single searchable unit in the offline RAG index."""

    doc_id: str
    title: str
    body: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RagChunkHit:
    """Retrieval result returned to the tutor agent."""

    doc_id: str
    score: float
    title: str
    body: str
    metadata: dict[str, Any]

    @classmethod
    def from_document(cls, document: RagDocument, score: float) -> RagChunkHit:
        return cls(
            doc_id=document.doc_id,
            score=score,
            title=document.title,
            body=document.body,
            metadata=dict(document.metadata),
        )
