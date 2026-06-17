"""Chroma vector store for lecture theory (ported from RAG_chemistry)."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.rag.embeddings import get_openai_embeddings


@lru_cache
def get_lectures_store():
    """Persistent Chroma collection for lecture chunks."""
    from langchain_chroma import Chroma

    settings = get_settings()
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=settings.chroma_lectures_collection,
        embedding_function=get_openai_embeddings(),
        persist_directory=str(settings.chroma_dir),
    )
