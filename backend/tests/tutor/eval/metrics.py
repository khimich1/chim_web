"""Retrieval quality metrics for the tutor RAG eval set."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.rag.documents import RagChunkHit
from app.services.rag.retriever import Retriever

from .corpus import EvalCase


@dataclass(frozen=True, slots=True)
class EvalResult:
    case: EvalCase
    hits: list[RagChunkHit]
    recalled: bool


def hit_matches_case(hit: RagChunkHit, case: EvalCase) -> bool:
    metadata = hit.metadata
    return (
        metadata.get("topic") == case.topic
        and metadata.get("chunk_idx") == case.chunk_idx
    )


def recall_at_k(
    retriever: Retriever,
    cases: list[EvalCase],
    *,
    k: int = 5,
) -> tuple[float, list[EvalResult]]:
    """Fraction of cases where the expected topic+chunk_idx appears in top-k hits."""
    if not cases:
        return 0.0, []

    results: list[EvalResult] = []
    recalled_count = 0
    for case in cases:
        hits = retriever.search(
            case.query,
            track=case.track,
            source=case.source,
            limit=k,
        )
        recalled = any(hit_matches_case(hit, case) for hit in hits)
        if recalled:
            recalled_count += 1
        results.append(EvalResult(case=case, hits=hits, recalled=recalled))

    return recalled_count / len(cases), results


def format_recall_report(
    label: str,
    recall: float,
    results: list[EvalResult],
    *,
    threshold: float,
) -> str:
    missed = [result for result in results if not result.recalled]
    lines = [
        f"{label}: recall@{len(results[0].hits) if results else 5}={recall:.3f} "
        f"(threshold {threshold:.2f})",
    ]
    for result in missed:
        top = result.hits[:3]
        top_desc = ", ".join(
            f"{hit.metadata.get('topic')}[{hit.metadata.get('chunk_idx')}]"
            for hit in top
        ) or "(no hits)"
        lines.append(
            f"  MISS: {result.case.query!r} "
            f"expected {result.case.topic}[{result.case.chunk_idx}] -> top: {top_desc}"
        )
    return "\n".join(lines)
