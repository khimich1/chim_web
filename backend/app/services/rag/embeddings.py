"""Embedding provider for Chroma RAG (ported from RAG_chemistry)."""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from app.core.config import get_settings


class EmbeddingsProvider(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


@lru_cache
def get_openai_embeddings():
    """Lazy OpenAI embeddings — only when langchain-openai is installed."""
    from langchain_openai import OpenAIEmbeddings

    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key or None,
    )
