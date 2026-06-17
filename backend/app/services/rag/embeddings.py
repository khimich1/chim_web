"""Embedding providers for RAG (OpenAI + deterministic test fallback)."""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Protocol

from app.core.config import Settings, get_settings
from app.services.rag.keyword import tokenize

_EMBEDDING_DIM = 1536


class EmbeddingsProvider(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class DeterministicEmbeddingsProvider:
    """Hash tokens into a fixed-size unit vector — for pytest without OpenAI."""

    def __init__(self, *, dimensions: int = _EMBEDDING_DIM) -> None:
        self._dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_text(text)

    def _embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        for token in tokenize(text):
            index = hash(token) % self._dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0.0:
            return vector
        return [value / norm for value in vector]


@lru_cache
def get_openai_embeddings():
    """Lazy OpenAI embeddings — only when langchain-openai is installed."""
    from langchain_openai import OpenAIEmbeddings

    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key or None,
    )


class OpenAIEmbeddingsProvider:
    """Adapter around langchain OpenAIEmbeddings."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return get_openai_embeddings().embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return get_openai_embeddings().embed_query(text)


def get_embeddings_provider(settings: Settings | None = None) -> EmbeddingsProvider | None:
    """Return OpenAI provider when configured; otherwise None (keyword fallback)."""
    app_settings = settings or get_settings()
    if not app_settings.openai_api_key:
        return None
    return OpenAIEmbeddingsProvider()


def embedding_text_for_document(title: str, body: str) -> str:
    """Text passed to the embedding model for a lecture chunk."""
    return f"{title}\n\n{body}".strip()
