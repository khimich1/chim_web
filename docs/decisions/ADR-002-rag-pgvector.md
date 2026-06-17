# ADR-002: pgvector for tutor RAG embeddings

## Status

Accepted

## Date

2026-06-17

## Context

The chemistry tutor needs hybrid retrieval (keyword ∪ embeddings) for lecture chunks.
`RAG_chemistry` used Chroma locally; `chim_web` already runs PostgreSQL for app data.

## Decision

Store offline-built embeddings in **pgvector** (`rag_embeddings` table) in the existing
PostgreSQL database. Keep the keyword index in `rag_index.json`. Enable hybrid search via
`RAG_HYBRID_ENABLED` with keyword-only fallback when embeddings or `OPENAI_API_KEY` are
missing. Chroma remains a dev-only interim tool, not used in production tutor retrieval.

## Alternatives Considered

### Chroma only — rejected

Adds a second persistence layer beside PostgreSQL; harder to operate in Docker Compose.

### Elasticsearch — rejected

Operational overhead exceeds MVP needs for ~200 lecture chunks.

## Consequences

- Alembic migration `007_rag_embeddings` requires PostgreSQL with `vector` extension.
- CLI: `python -m app.cli.index_rag --embeddings` builds vectors offline.
- `Retriever.search()` signature unchanged; hybrid is transparent to tutor tools.
- pytest uses `InMemoryVectorStore` — no live PostgreSQL/pgvector required in CI.
