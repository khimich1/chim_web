"""Build or rebuild the offline RAG keyword index from content SQLite DBs."""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.core.config import get_settings
from app.services.rag.embeddings import (
    embedding_text_for_document,
    get_embeddings_provider,
)
from app.services.rag.ingestion import ingest_all_documents
from app.services.rag.pgvector_store import PgVectorStore, index_documents_to_store
from app.services.rag.retriever import Retriever


async def _rebuild_pgvector(settings) -> int:
    provider = get_embeddings_provider(settings)
    if provider is None:
        print(
            "Skipping pgvector index: OPENAI_API_KEY is not set "
            "(keyword-only fallback remains available).",
            file=sys.stderr,
        )
        return 0

    documents = ingest_all_documents(settings)
    embed_texts = [
        embedding_text_for_document(document.title, document.body)
        for document in documents
    ]
    store = PgVectorStore.from_settings(settings)
    try:
        count = index_documents_to_store(
            store,
            documents,
            embed_texts=embed_texts,
            embeddings_provider=provider,
        )
        return count
    finally:
        await store.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build offline RAG indexes from content SQLite DBs"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Re-ingest content databases and rebuild keyword metadata in PostgreSQL",
    )
    parser.add_argument(
        "--embeddings",
        action="store_true",
        help="Build pgvector embedding index in PostgreSQL (requires OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--chroma",
        action="store_true",
        help="(Legacy dev-only) rebuild Chroma index — not used in tutor hot path",
    )
    args = parser.parse_args(argv)

    if not args.rebuild and not args.embeddings and not args.chroma:
        parser.error("Pass --rebuild, --embeddings, and/or --chroma")

    settings = get_settings()

    if args.rebuild:
        if not settings.database_url.startswith("postgresql"):
            print(
                "Keyword rebuild requires PostgreSQL DATABASE_URL; skipping.",
                file=sys.stderr,
            )
        else:
            retriever = Retriever([])
            count = retriever.rebuild_index(settings)
            print(f"Keyword index rebuilt: {count} documents in rag_documents (PostgreSQL)")

    if args.embeddings:
        if not settings.database_url.startswith("postgresql"):
            print(
                "pgvector index requires PostgreSQL DATABASE_URL; skipping.",
                file=sys.stderr,
            )
        else:
            count = asyncio.run(_rebuild_pgvector(settings))
            if count:
                print(f"pgvector index rebuilt: {count} documents")

    if args.chroma:
        from app.services.rag.chroma_ingestion import ingest_lectures_to_chroma

        chroma_count = ingest_lectures_to_chroma(settings, rebuild=True)
        print(f"Chroma index rebuilt: {chroma_count} lecture chunks -> {settings.chroma_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
