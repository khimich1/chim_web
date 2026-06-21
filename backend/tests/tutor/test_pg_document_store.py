"""Tests for PostgreSQL keyword document store (Task 96)."""

from __future__ import annotations

from app.services.rag.documents import RagDocument
from app.services.rag.pg_document_store import InMemoryDocumentStore


def test_in_memory_document_store_roundtrip() -> None:
    documents = [
        RagDocument(
            doc_id="lecture:Алканы:0",
            title="Алканы — Свойства",
            body="Алканы малореакционны.",
            metadata={"source": "lecture", "topic": "Алканы", "chunk_idx": 0},
        )
    ]
    store = InMemoryDocumentStore()

    assert store.rebuild(documents) == 1
    assert store.count() == 1
    loaded = store.load_all()
    assert loaded[0].doc_id == documents[0].doc_id
    assert loaded[0].metadata["topic"] == "Алканы"


def test_in_memory_rebuild_replaces_previous_documents() -> None:
    store = InMemoryDocumentStore()
    first = [
        RagDocument(
            doc_id="lecture:A:0",
            title="A",
            body="first",
            metadata={"source": "lecture", "topic": "A"},
        )
    ]
    second = [
        RagDocument(
            doc_id="lecture:B:0",
            title="B",
            body="second",
            metadata={"source": "lecture", "topic": "B"},
        )
    ]

    store.rebuild(first)
    store.rebuild(second)

    assert store.count() == 1
    assert store.load_all()[0].metadata["topic"] == "B"
