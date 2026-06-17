"""Hybrid retrieval tests with in-memory vector store (Task 41.2)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.core.config import Settings
from app.services.rag.embeddings import (
    DeterministicEmbeddingsProvider,
    embedding_text_for_document,
)
from app.services.rag.ingestion import ingest_all_documents_from_paths
from app.services.rag.pgvector_store import InMemoryVectorStore, index_documents_to_store
from app.services.rag.retriever import Retriever


def _create_carbonic_acids_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE prepared_lectures (
            topic TEXT NOT NULL,
            chunk_idx INTEGER NOT NULL,
            chunk_title TEXT,
            lecture TEXT,
            qa_questions TEXT,
            qa_answers TEXT,
            PRIMARY KEY (topic, chunk_idx)
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO prepared_lectures (topic, chunk_idx, chunk_title, lecture)
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                "Карбоновые кислоты",
                1,
                "Свойства и изомерия карбоновых кислот",
                "Изомерия карбоновых кислот и физические свойства насыщенных кислот.",
            ),
            (
                "Карбоновые кислоты",
                2,
                "Получение карбоновых кислот",
                "### Химические свойства\n\n"
                "Кислоты реагируют с основаниями; типичны для карбоновых соединений.",
            ),
        ],
    )
    conn.commit()
    conn.close()


@pytest.fixture
def hybrid_retriever(tmp_path: Path) -> Retriever:
    lectures = tmp_path / "prepared_lectures.db"
    _create_carbonic_acids_db(lectures)
    documents = ingest_all_documents_from_paths(lectures_db_path=lectures)
    provider = DeterministicEmbeddingsProvider()
    store = InMemoryVectorStore()
    embed_texts = [
        embedding_text_for_document(document.title, document.body)
        for document in documents
    ]
    index_documents_to_store(
        store,
        documents,
        embed_texts=embed_texts,
        embeddings_provider=provider,
    )
    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
        jwt_secret="test-secret",
        content_lectures_db_path=lectures,
        rag_hybrid_enabled=True,
        openai_api_key="test-key",
    )
    return Retriever(
        documents,
        settings=settings,
        vector_store=store,
        embeddings_provider=provider,
    )


def test_keyword_only_ignores_vector_store(hybrid_retriever: Retriever) -> None:
    keyword_only = Retriever(
        hybrid_retriever._documents,  # noqa: SLF001
        settings=Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
            jwt_secret="test-secret",
            rag_hybrid_enabled=False,
        ),
    )
    hits = keyword_only.search(
        "изомерия карбоновых кислот",
        track="ege",
        limit=1,
    )
    assert hits
    assert hits[0].metadata.get("chunk_idx") == 1


def test_hybrid_search_path_used_when_store_configured(
    hybrid_retriever: Retriever,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"hybrid": False}

    def _spy(*args, **kwargs):
        called["hybrid"] = True
        return Retriever._hybrid_search(hybrid_retriever, *args, **kwargs)

    monkeypatch.setattr(hybrid_retriever, "_hybrid_search", _spy)
    hits = hybrid_retriever.search(
        "химические свойства карбоновых кислот",
        track="ege",
        limit=1,
    )
    assert called["hybrid"]
    assert hits


def test_hybrid_falls_back_to_keyword_without_vector_store(
    hybrid_retriever: Retriever,
) -> None:
    fallback = Retriever(
        hybrid_retriever._documents,  # noqa: SLF001
        settings=Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            jwt_secret="test-secret",
            rag_hybrid_enabled=True,
            openai_api_key="test-key",
        ),
        embeddings_provider=DeterministicEmbeddingsProvider(),
    )
    hits = fallback.search("изомерия карбоновых кислот", track="ege", limit=1)
    assert hits
    assert hits[0].metadata.get("topic") == "Карбоновые кислоты"


def test_hybrid_falls_back_without_openai_key(hybrid_retriever: Retriever) -> None:
    fallback = Retriever(
        hybrid_retriever._documents,  # noqa: SLF001
        settings=Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
            jwt_secret="test-secret",
            rag_hybrid_enabled=True,
            openai_api_key="",
        ),
        vector_store=InMemoryVectorStore(),
    )
    hits = fallback.search("изомерия карбоновых кислот", track="ege", limit=1)
    assert hits
    assert hits[0].metadata.get("chunk_idx") == 1
