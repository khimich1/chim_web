"""Build or rebuild the offline RAG keyword index from content SQLite DBs."""

from __future__ import annotations

import argparse
import sys

from app.core.config import get_settings
from app.services.rag.retriever import Retriever


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build offline RAG indexes from content SQLite DBs"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Re-ingest content databases and overwrite the keyword index file",
    )
    parser.add_argument(
        "--chroma",
        action="store_true",
        help="Also rebuild Chroma vector index for lectures (requires OPENAI_API_KEY)",
    )
    args = parser.parse_args(argv)

    if not args.rebuild and not args.chroma:
        parser.error("Pass --rebuild and/or --chroma")

    settings = get_settings()

    if args.rebuild:
        retriever = Retriever([])
        count = retriever.rebuild_index(settings)
        print(f"Keyword index rebuilt: {count} documents -> {settings.rag_index_path}")

    if args.chroma:
        from app.services.rag.chroma_ingestion import ingest_lectures_to_chroma

        chroma_count = ingest_lectures_to_chroma(settings, rebuild=True)
        print(f"Chroma index rebuilt: {chroma_count} lecture chunks -> {settings.chroma_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
