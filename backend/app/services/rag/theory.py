"""Theory search for the tutor agent (keyword index; Chroma optional later)."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.services.rag.documents import ExamTrack
from app.services.rag.retriever import Retriever


@dataclass(frozen=True, slots=True)
class TheoryHit:
    content: str
    topic: str
    chunk_title: str
    chunk_idx: int | None = None
    score: float | None = None
    source: str | None = None


def search_theory(
    query: str,
    *,
    track: ExamTrack,
    top_k: int | None = None,
    retriever: Retriever | None = None,
    page_context_topic: str | None = None,
) -> list[TheoryHit]:
    """Find lecture fragments for tutor tools (no correct_ans / test keys)."""
    settings = get_settings()
    rag = retriever or Retriever.from_settings()
    limit = top_k or settings.rag_top_k

    hits = rag.search_with_rewrite(
        query,
        track=track,
        limit=limit,
        page_context_topic=page_context_topic,
    )
    theory_hits: list[TheoryHit] = []
    for hit in hits:
        source = hit.metadata.get("source")
        if source not in {"lecture", "lecture_qa"}:
            continue
        theory_hits.append(
            TheoryHit(
                content=hit.body,
                topic=str(hit.metadata.get("topic", "")),
                chunk_title=str(hit.metadata.get("chunk_title", "")),
                chunk_idx=hit.metadata.get("chunk_idx"),
                score=hit.score,
                source=source,
            )
        )
        if len(theory_hits) >= limit:
            break
    return theory_hits
