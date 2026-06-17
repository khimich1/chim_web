"""Hybrid retrieval fusion: RRF merge and dedup by topic+chunk_idx (Task 41.2 / A5)."""

from __future__ import annotations

from app.services.rag.documents import RagChunkHit

_SOURCE_PRIORITY = {"lecture": 0, "lecture_qa": 1}


def reciprocal_rank_fusion(
    ranked_doc_ids: list[list[str]],
    *,
    k: int = 60,
) -> dict[str, float]:
    """Combine ranked lists with reciprocal rank fusion."""
    scores: dict[str, float] = {}
    for ranked in ranked_doc_ids:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return scores


def dedup_key(hit: RagChunkHit) -> tuple[str, int | None]:
    topic = str(hit.metadata.get("topic", ""))
    chunk_idx = hit.metadata.get("chunk_idx")
    return topic, chunk_idx if isinstance(chunk_idx, int) else None


def dedup_hits(hits: list[RagChunkHit]) -> list[RagChunkHit]:
    """Keep one hit per topic+chunk_idx; prefer lecture over lecture_qa on tie."""
    best_by_key: dict[tuple[str, int | None], RagChunkHit] = {}
    for hit in hits:
        key = dedup_key(hit)
        current = best_by_key.get(key)
        if current is None or _is_preferred(hit, current):
            best_by_key[key] = hit
    return list(best_by_key.values())


def _is_preferred(candidate: RagChunkHit, incumbent: RagChunkHit) -> bool:
    if candidate.score > incumbent.score:
        return True
    if candidate.score < incumbent.score:
        return False
    cand_source = str(candidate.metadata.get("source", ""))
    inc_source = str(incumbent.metadata.get("source", ""))
    cand_pri = _SOURCE_PRIORITY.get(cand_source, 99)
    inc_pri = _SOURCE_PRIORITY.get(inc_source, 99)
    return cand_pri < inc_pri


def hybrid_rerank(
    keyword_hits: list[RagChunkHit],
    vector_hits: list[RagChunkHit],
    *,
    pool_size: int = 10,
    limit: int = 4,
) -> list[RagChunkHit]:
    """Merge keyword and vector candidates with RRF, dedup, return top limit."""
    keyword_pool = keyword_hits[:pool_size]
    vector_pool = vector_hits[:pool_size]

    hits_by_id: dict[str, RagChunkHit] = {}
    for hit in keyword_pool + vector_pool:
        hits_by_id.setdefault(hit.doc_id, hit)

    fused_scores = reciprocal_rank_fusion(
        [
            [hit.doc_id for hit in keyword_pool],
            [hit.doc_id for hit in vector_pool],
        ]
    )

    fused_hits: list[RagChunkHit] = []
    for doc_id, score in fused_scores.items():
        base = hits_by_id[doc_id]
        fused_hits.append(
            RagChunkHit(
                doc_id=base.doc_id,
                score=score,
                title=base.title,
                body=base.body,
                metadata=dict(base.metadata),
            )
        )

    fused_hits.sort(key=lambda hit: hit.score, reverse=True)
    deduped = dedup_hits(fused_hits)
    deduped.sort(key=lambda hit: hit.score, reverse=True)
    return deduped[:limit]
