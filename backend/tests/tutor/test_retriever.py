"""Tests for offline RAG ingestion and keyword retrieval (Task 31)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.services.rag.ingestion import ingest_all_documents_from_paths
from app.services.rag.pg_document_store import InMemoryDocumentStore
from app.services.rag.retriever import Retriever
from app.services.rag.store import load_index, save_index


def test_ingestion_indexes_only_lectures_without_correct_ans(
    rag_content_dbs: dict[str, Path],
) -> None:
    documents = ingest_all_documents_from_paths(
        lectures_db_path=rag_content_dbs["lectures"],
    )

    bodies = "\n".join(document.body for document in documents)
    assert "secret-answer" not in bodies
    assert any(document.metadata.get("source") == "lecture" for document in documents)
    assert any(document.metadata.get("source") == "lecture_qa" for document in documents)
    assert not any(document.metadata.get("source") == "test" for document in documents)
    assert all(
        document.metadata.get("source") in {"lecture", "lecture_qa"}
        for document in documents
    )


def test_search_finds_relevant_lecture_in_top_three(rag_retriever: Retriever) -> None:
    hits = rag_retriever.search(
        "почему алканы малореакционны",
        track="ege",
        limit=3,
    )

    assert hits
    top_topics = {hit.metadata.get("topic") for hit in hits}
    assert "Алканы" in top_topics
    assert hits[0].metadata.get("source") in {"lecture", "lecture_qa"}


def test_index_has_no_test_source_documents(rag_retriever: Retriever) -> None:
    assert not any(
        document.metadata.get("source") == "test"
        for document in rag_retriever._documents  # noqa: SLF001 — assert index contents
    )
    assert rag_retriever.search("разбор задания", track="ege", source="test") == []


def test_lecture_documents_visible_for_both_tracks(rag_retriever: Retriever) -> None:
    for track in ("ege", "oge"):
        hits = rag_retriever.search("ионные соединения", track=track, source="lecture")
        assert hits
        assert hits[0].metadata.get("topic") == "Соли"


def test_empty_query_returns_no_hits(rag_retriever: Retriever) -> None:
    assert rag_retriever.search("   ", track="ege") == []


def test_index_roundtrip(tmp_path: Path, rag_retriever: Retriever) -> None:
    index_path = tmp_path / "rag_index.json"
    save_index(rag_retriever._documents, index_path)  # noqa: SLF001 — test internal store

    loaded = Retriever.from_index_path(index_path)
    hits = loaded.search("алканы малореакционны", track="ege", limit=1)

    assert hits
    assert hits[0].metadata.get("topic") == "Алканы"


def test_rebuild_index_persists_documents_to_pg(
    tmp_path: Path,
    rag_content_dbs: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core.config import Settings

    store = InMemoryDocumentStore()
    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
        jwt_secret="test-secret",
        content_ege_db_path=rag_content_dbs["ege"],
        content_oge_db_path=rag_content_dbs["oge"],
        content_lectures_db_path=rag_content_dbs["lectures"],
        rag_index_path=tmp_path / "rag_index.json",
        rag_hybrid_enabled=False,
    )
    monkeypatch.setattr("app.services.rag.retriever.get_settings", lambda: settings)

    retriever = Retriever([])
    count = retriever.rebuild_index(settings, document_store=store)

    assert count >= 3
    assert store.count() == count
    reloaded = Retriever(store.load_all(), settings=settings)
    hits = reloaded.search("алканы малореакционны", track="ege", limit=1)
    assert hits
    assert hits[0].metadata.get("topic") == "Алканы"


def test_from_settings_does_not_read_json_index(
    tmp_path: Path,
    rag_content_dbs: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core.config import Settings

    index_path = tmp_path / "rag_index.json"
    documents = ingest_all_documents_from_paths(
        lectures_db_path=rag_content_dbs["lectures"],
    )
    save_index(documents, index_path)

    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
        jwt_secret="test-secret",
        content_lectures_db_path=rag_content_dbs["lectures"],
        rag_index_path=index_path,
    )
    monkeypatch.setattr("app.services.rag.retriever.get_settings", lambda: settings)
    monkeypatch.setattr(
        "app.services.rag.retriever.load_documents_from_settings",
        lambda _settings=None: [],
    )
    load_index_mock = MagicMock(side_effect=AssertionError("json index must not load"))
    monkeypatch.setattr("app.services.rag.retriever.load_index", load_index_mock)

    retriever = Retriever.from_settings(settings)

    assert retriever.document_count == 0
    load_index_mock.assert_not_called()
