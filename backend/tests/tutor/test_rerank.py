"""Unit tests for hybrid RRF fusion and dedup (Task 41.2)."""

from __future__ import annotations

from app.services.rag.documents import RagChunkHit
from app.services.rag.rerank import dedup_hits, hybrid_rerank, reciprocal_rank_fusion


def _hit(
    doc_id: str,
    *,
    score: float,
    topic: str,
    chunk_idx: int,
    source: str,
) -> RagChunkHit:
    return RagChunkHit(
        doc_id=doc_id,
        score=score,
        title=doc_id,
        body=doc_id,
        metadata={"topic": topic, "chunk_idx": chunk_idx, "source": source},
    )


def test_reciprocal_rank_fusion_combines_both_lists() -> None:
    scores = reciprocal_rank_fusion(
        [
            ["a", "b", "c"],
            ["b", "d"],
        ]
    )
    assert scores["b"] > scores["a"]
    assert scores["b"] > scores["d"]


def test_dedup_prefers_lecture_over_lecture_qa_on_tie() -> None:
    lecture = _hit(
        "lecture:Тема:1",
        score=1.0,
        topic="Тема",
        chunk_idx=1,
        source="lecture",
    )
    qa = _hit(
        "lecture_qa:Тема:1:0",
        score=1.0,
        topic="Тема",
        chunk_idx=1,
        source="lecture_qa",
    )
    deduped = dedup_hits([qa, lecture])
    assert len(deduped) == 1
    assert deduped[0].metadata["source"] == "lecture"


def test_hybrid_rerank_promotes_vector_only_candidate() -> None:
    keyword_hits = [
        _hit(
            "lecture:А:0",
            score=3.0,
            topic="А",
            chunk_idx=0,
            source="lecture",
        )
    ]
    vector_hits = [
        _hit(
            "lecture:Б:2",
            score=0.9,
            topic="Б",
            chunk_idx=2,
            source="lecture",
        ),
        _hit(
            "lecture:А:0",
            score=0.5,
            topic="А",
            chunk_idx=0,
            source="lecture",
        ),
    ]
    merged = hybrid_rerank(keyword_hits, vector_hits, pool_size=10, limit=2)
    doc_ids = [hit.doc_id for hit in merged]
    assert "lecture:Б:2" in doc_ids
