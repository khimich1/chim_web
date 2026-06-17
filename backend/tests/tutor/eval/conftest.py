"""Shared fixtures for RAG eval tests."""

from __future__ import annotations

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

from .corpus import EVAL_CASES, create_eval_lectures_db


@pytest.fixture
def eval_lectures_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "eval_prepared_lectures.db"
    create_eval_lectures_db(db_path)
    return db_path


@pytest.fixture
def eval_documents(eval_lectures_db: Path):
    return ingest_all_documents_from_paths(lectures_db_path=eval_lectures_db)


@pytest.fixture
def eval_vector_store(eval_documents, eval_lectures_db: Path) -> InMemoryVectorStore:
    provider = DeterministicEmbeddingsProvider()
    store = InMemoryVectorStore()
    embed_texts = [
        embedding_text_for_document(document.title, document.body)
        for document in eval_documents
    ]
    index_documents_to_store(
        store,
        eval_documents,
        embed_texts=embed_texts,
        embeddings_provider=provider,
    )
    return store


@pytest.fixture
def eval_embeddings_provider() -> DeterministicEmbeddingsProvider:
    return DeterministicEmbeddingsProvider()


@pytest.fixture
def eval_hybrid_settings(eval_lectures_db: Path) -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
        jwt_secret="test-secret",
        content_lectures_db_path=eval_lectures_db,
        rag_hybrid_enabled=True,
        openai_api_key="test-key",
    )


@pytest.fixture
def eval_hybrid_retriever(
    eval_documents,
    eval_vector_store: InMemoryVectorStore,
    eval_embeddings_provider: DeterministicEmbeddingsProvider,
    eval_hybrid_settings: Settings,
) -> Retriever:
    return Retriever(
        eval_documents,
        settings=eval_hybrid_settings,
        vector_store=eval_vector_store,
        embeddings_provider=eval_embeddings_provider,
    )


@pytest.fixture
def eval_keyword_retriever(eval_documents) -> Retriever:
    return Retriever(
        eval_documents,
        settings=Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/chemistry",
            jwt_secret="test-secret",
            rag_hybrid_enabled=False,
        ),
    )


@pytest.fixture
def eval_cases():
    return list(EVAL_CASES)
