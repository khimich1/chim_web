"""Persist and load the offline keyword RAG index."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services.rag.documents import RagDocument

_INDEX_VERSION = 1


def _document_to_dict(document: RagDocument) -> dict[str, Any]:
    return {
        "doc_id": document.doc_id,
        "title": document.title,
        "body": document.body,
        "metadata": document.metadata,
    }


def _document_from_dict(payload: dict[str, Any]) -> RagDocument:
    return RagDocument(
        doc_id=str(payload["doc_id"]),
        title=str(payload["title"]),
        body=str(payload["body"]),
        metadata=dict(payload.get("metadata") or {}),
    )


def save_index(documents: list[RagDocument], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": _INDEX_VERSION,
        "documents": [_document_to_dict(document) for document in documents],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_index(path: Path) -> list[RagDocument]:
    if not path.is_file():
        raise FileNotFoundError(f"RAG index not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != _INDEX_VERSION:
        raise ValueError(f"Unsupported RAG index version: {payload.get('version')}")
    return [_document_from_dict(item) for item in payload.get("documents", [])]
