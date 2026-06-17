"""RAG retrieval eval: recall@5 on the reference question set (Task 41.3)."""

from __future__ import annotations

import pytest

from app.services.rag.retriever import Retriever

from .metrics import format_recall_report, recall_at_k

RECALL_THRESHOLD = 0.8
RECALL_K = 5


def test_carbonic_acids_chemical_properties_in_top_five(
    eval_hybrid_retriever: Retriever,
) -> None:
    """AC-16.5 anchor case: «химические свойства карбоновых кислот» → chunk [2]."""
    hits = eval_hybrid_retriever.search(
        "химические свойства карбоновых кислот",
        track="ege",
        limit=RECALL_K,
    )
    chunk_indices = [
        hit.metadata.get("chunk_idx")
        for hit in hits
        if hit.metadata.get("topic") == "Карбоновые кислоты"
    ]
    assert 2 in chunk_indices


def test_hybrid_recall_at_five_meets_threshold(
    eval_hybrid_retriever: Retriever,
    eval_cases,
) -> None:
    recall, results = recall_at_k(eval_hybrid_retriever, eval_cases, k=RECALL_K)
    report = format_recall_report(
        "hybrid",
        recall,
        results,
        threshold=RECALL_THRESHOLD,
    )
    assert recall >= RECALL_THRESHOLD, report


def test_hybrid_recall_at_least_keyword_only(
    eval_hybrid_retriever: Retriever,
    eval_keyword_retriever: Retriever,
    eval_cases,
) -> None:
    hybrid_recall, _ = recall_at_k(eval_hybrid_retriever, eval_cases, k=RECALL_K)
    keyword_recall, _ = recall_at_k(eval_keyword_retriever, eval_cases, k=RECALL_K)
    assert hybrid_recall >= keyword_recall, (
        f"hybrid recall@{RECALL_K}={hybrid_recall:.3f} "
        f"< keyword-only={keyword_recall:.3f}"
    )


def test_sulfur_metals_case_in_top_five_with_rewrite(
    eval_rewrite_retriever: Retriever,
) -> None:
    """AC-16.7: «сера + металлы» → Cера chunk [1] after query rewriting."""
    hits = eval_rewrite_retriever.search_with_rewrite(
        "как с металлами реагирует сера?",
        track="ege",
        limit=RECALL_K,
    )
    assert any(
        hit.metadata.get("topic") == "Сера" and hit.metadata.get("chunk_idx") == 1
        for hit in hits
    )


def test_rewrite_recall_at_five_meets_threshold(
    eval_rewrite_retriever: Retriever,
    eval_cases,
) -> None:
    recall, results = recall_at_k(
        eval_rewrite_retriever,
        eval_cases,
        k=RECALL_K,
        use_rewrite=True,
    )
    report = format_recall_report(
        "hybrid+rewrite",
        recall,
        results,
        threshold=RECALL_THRESHOLD,
    )
    assert recall >= RECALL_THRESHOLD, report


def test_rewrite_improves_sulfur_case_over_single_query(
    eval_hybrid_retriever: Retriever,
    eval_rewrite_retriever: Retriever,
) -> None:
    query = "как с металлами реагирует сера?"
    single = eval_hybrid_retriever.search(query, track="ege", limit=RECALL_K)
    rewritten = eval_rewrite_retriever.search_with_rewrite(
        query,
        track="ege",
        limit=RECALL_K,
    )
    single_ok = any(
        hit.metadata.get("topic") == "Сера" and hit.metadata.get("chunk_idx") == 1
        for hit in single
    )
    rewrite_ok = any(
        hit.metadata.get("topic") == "Сера" and hit.metadata.get("chunk_idx") == 1
        for hit in rewritten
    )
    assert rewrite_ok, "expected Сера[1] in top-5 with query rewrite"
    if not single_ok:
        pytest.skip("single-query miss is the regression this slice fixes")

