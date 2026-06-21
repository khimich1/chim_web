# ADR-002: pgvector for tutor RAG embeddings

## Status

Accepted (updated 2026-06-21 — Task 96 pg-only hot path)

## Date

2026-06-17

## Context

The chemistry tutor needs hybrid retrieval (keyword ∪ embeddings) for lecture chunks.
`RAG_chemistry` used Chroma locally; `chim_web` already runs PostgreSQL for app data.

## Decision

Store **keyword metadata** in PostgreSQL (`rag_documents` table) and **embeddings** in
**pgvector** (`rag_embeddings` table) in the existing PostgreSQL database. Enable hybrid
search via `RAG_HYBRID_ENABLED` with keyword-only fallback when embeddings or
`OPENAI_API_KEY` are missing.

**Production hot path (Task 96):**

- `Retriever.from_settings()` loads documents from `rag_documents` — no `rag_index.json`
  read per request.
- CLI `python -m app.cli.index_rag --rebuild` writes keyword metadata to PostgreSQL.
- CLI `--embeddings` builds pgvector rows offline.
- Chroma remains a **legacy dev-only** CLI flag (`--chroma`); not used in tutor retrieval.

## Alternatives Considered

### Chroma only — rejected

Adds a second persistence layer beside PostgreSQL; harder to operate in Docker Compose.

### Keep `rag_index.json` for keyword index — superseded (Task 96)

File-based index duplicated PG metadata and was read on every `from_settings()` call when
present. Moved to `rag_documents` for single persistence backend.

### Elasticsearch — rejected

Operational overhead exceeds MVP needs for ~200 lecture chunks.

## Consequences

- Alembic migrations: `007_rag_embeddings` (pgvector), `016_rag_documents` (keyword metadata).
- CLI: `--rebuild` for keyword metadata; `--embeddings` for vectors.
- `Retriever.search()` signature unchanged; hybrid is transparent to tutor tools.
- pytest uses in-memory document/vector stores — no live PostgreSQL/pgvector required in CI.
- `rag_index.json` / `RAG_INDEX_PATH` retained only for non-PostgreSQL dev fallback in
  `rebuild_index()`; not used in production retrieval path.
