"""Query rewriting tests (Task 41.4)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.config import Settings
from app.services.rag.ingestion import ingest_all_documents_from_paths
from app.services.rag.query_rewrite import rewrite_queries
from app.services.rag.retriever import Retriever

from tests.tutor.eval.corpus import create_eval_lectures_db


@pytest.fixture
def rewrite_eval_retriever(tmp_path: Path) -> Retriever:
    lectures_db = tmp_path / "eval_lectures.db"
    create_eval_lectures_db(lectures_db)
    documents = ingest_all_documents_from_paths(lectures_db_path=lectures_db)
    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
        jwt_secret="test-secret",
        content_lectures_db_path=lectures_db,
        rag_hybrid_enabled=False,
        rag_query_rewrite_enabled=True,
        openai_api_key="",
    )
    return Retriever(documents, settings=settings)


def test_rewrite_sulfur_metals_produces_multiple_variants() -> None:
    queries = rewrite_queries(
        "как с металлами реагирует сера?",
        settings=Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
            jwt_secret="test-secret",
            openai_api_key="",
        ),
    )
    assert len(queries) >= 2
    assert queries[0] == "как с металлами реагирует сера?"
    joined = " ".join(queries).lower()
    assert "сера" in joined
    assert "сульфид" in joined or "cus" in joined or "cas" in joined


def test_rewrite_respects_max_three_queries() -> None:
    queries = rewrite_queries(
        "как с металлами реагирует сера?",
        settings=Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
            jwt_secret="test-secret",
            openai_api_key="",
        ),
    )
    assert len(queries) <= 3


def test_rewrite_disabled_via_empty_question_returns_empty() -> None:
    assert rewrite_queries("   ") == []


def test_rewrite_adds_page_context_topic_when_question_mentions_it() -> None:
    queries = rewrite_queries(
        "расскажи про алканы",
        page_context_topic="Алканы",
        settings=Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
            jwt_secret="test-secret",
            openai_api_key="",
        ),
    )
    assert any("Алканы" in query for query in queries)


def test_rewrite_falls_back_to_rules_when_llm_unavailable() -> None:
    with patch(
        "app.services.rag.query_rewrite._rewrite_with_llm",
        return_value=None,
    ):
        queries = rewrite_queries(
            "химические свойства карбоновых кислот",
            settings=Settings(
                database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
                jwt_secret="test-secret",
                openai_api_key="sk-test",
            ),
        )
    assert queries
    assert queries[0] == "химические свойства карбоновых кислот"


def test_rewrite_uses_llm_variants_when_available() -> None:
    with patch(
        "app.services.rag.query_rewrite._rewrite_with_llm",
        return_value=["сера CuS", "реакции серы"],
    ):
        queries = rewrite_queries(
            "как с металлами реагирует сера?",
            settings=Settings(
                database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
                jwt_secret="test-secret",
                openai_api_key="sk-test",
            ),
        )
    assert "сера CuS" in queries
    assert "реакции серы" in queries


def test_rewrite_falls_back_to_rules_when_llm_returns_none() -> None:
    with patch(
        "app.services.rag.query_rewrite._rewrite_with_llm",
        return_value=None,
    ):
        queries = rewrite_queries(
            "как с металлами реагирует сера?",
            settings=Settings(
                database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
                jwt_secret="test-secret",
                openai_api_key="sk-test",
            ),
        )
    assert len(queries) >= 2
    assert "сера" in " ".join(queries).lower()


def test_search_with_rewrite_disabled_uses_single_query(
    rewrite_eval_retriever: Retriever,
) -> None:
    """Feature flag off: search_with_rewrite must match search()."""
    query = "как с металлами реагирует сера?"
    disabled_settings = rewrite_eval_retriever._settings.model_copy(  # noqa: SLF001
        update={"rag_query_rewrite_enabled": False},
    )
    retriever = Retriever(
        rewrite_eval_retriever._documents,  # noqa: SLF001
        settings=disabled_settings,
    )
    single = retriever.search(query, track="ege", limit=5)
    via_rewrite = retriever.search_with_rewrite(query, track="ege", limit=5)
    assert via_rewrite == single


def test_search_multi_merges_rewrite_variants_for_sulfur_case(
    rewrite_eval_retriever: Retriever,
) -> None:
    """Multi-query path finds Сера[1] when naive single-query may miss it."""
    query = "как с металлами реагирует сера?"
    single = rewrite_eval_retriever.search(query, track="ege", limit=5)
    merged = rewrite_eval_retriever.search_with_rewrite(query, track="ege", limit=5)

    def _has_sulfur_chunk(hits) -> bool:
        return any(
            hit.metadata.get("topic") == "Сера" and hit.metadata.get("chunk_idx") == 1
            for hit in hits
        )

    assert _has_sulfur_chunk(merged)
    if not _has_sulfur_chunk(single):
        assert len(merged) >= len(single) or merged != single
