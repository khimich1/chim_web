# RAG retrieval eval (Task 41.3)

Reference question set for **recall@5** on tutor lecture retrieval. Runs in `pytest`
without a real LLM — embeddings use `DeterministicEmbeddingsProvider` and
`InMemoryVectorStore` (same pattern as `test_hybrid_retriever.py`).

## Run

```bash
cd backend
pytest tests/tutor/eval/ -v
```

## Dataset

- **Corpus:** `corpus.py` — 15 lecture chunks across 11 chemistry topics (synthetic SQLite DB).
- **Cases:** 15 queries with expected `topic` + `chunk_idx` (including the anchor case
  «химические свойства карбоновых кислот» → `Карбоновые кислоты` chunk `2`).
- **Metric:** recall@5 = share of cases where the expected chunk appears in the top-5 hits.

Threshold: **≥ 0.8** (AC-16.5).

## Keyword-only vs hybrid vs rewrite (deterministic fixtures)

| Mode | recall@5 | Notes |
|------|----------|-------|
| keyword-only | 0.93 (14/15) | Strong on exact terminology |
| hybrid (keyword ∪ vector + RRF) | 0.93 (14/15) | Anchor carbonic-acids case includes chunk `[2]` in top-5 |
| hybrid + query rewrite | ≥ 0.8 (16 cases) | Fixes «сера + металлы» via multi-query (Task 41.4) |

Hybrid does not always outrank keyword on every query (e.g. carbonic acids: chunk `[1]` may
still rank above `[2]` in title-heavy keyword scoring), but both chunks are in top-5 and the
eval checks **recall**, not MRR@1.

The **sulfur + metals** case (`как с металлами реагирует сера?` → `Сера` chunk `1`) is a
regression control for query rewriting: single-query hybrid may miss it when «металлы»
dominates scoring; `search_with_rewrite` should recall it via rule-based variants.

Production embeddings (`text-embedding-3-small` + pgvector) are expected to improve
semantic matches further; this eval guards regressions in the retrieval pipeline itself.

## Files

| File | Role |
|------|------|
| `corpus.py` | Lecture chunks + `EvalCase` list |
| `metrics.py` | `recall_at_k`, hit matching |
| `conftest.py` | Hybrid/keyword retriever fixtures |
| `test_recall.py` | AC-16.5 assertions |
