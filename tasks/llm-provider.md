# Implementation Plan: LLM Provider (DeepSeek → GigaChat)

## Overview

Тонкая фабрика chat-LLM для AI-репетитора: DeepSeek (OpenAI-compat) сейчас, контракт под GigaChat later. Embeddings/hybrid RAG не трогаем. Spec: [`docs/specs/llm-provider.md`](../docs/specs/llm-provider.md) (**approved**).

## Architecture Decisions

- Канон env: `LLM_*`; `OPENAI_*` — aliases для effective key/model (RAG продолжает читать `openai_api_key`).
- Одна фабрика `build_chat_llm` в `backend/app/services/tutor/llm.py`.
- `LLM_PROVIDER=gigachat` до адаптера → 503 на request, app стартует.
- Health: `llm_configured` + legacy `openai_configured` (одинаковое значение).
- Нет новых pip-зависимостей в increment 1.

## Task List

### Phase 1: Foundation (Increment 1) — **this session**

- [x] Task 1: Settings `LLM_*` + `effective_*` / `llm_configured`
- [x] Task 2: Factory `build_chat_llm` + unit tests
- [x] Task 3: Wire graph / tutor_service / health schemas
- [x] Task 4: `.env.example` + frontend health text/types
- [x] Task 5: Soften types to `BaseChatModel` where easy; update API tests

### Checkpoint: Increment 1

- [x] `pytest tests/tutor/ -q` зелёный
- [ ] App starts with `LLM_PROVIDER=gigachat` (no import crash) — covered by API 503 test
- [ ] Manual DeepSeek smoke (ops) — outside CI

### Phase 2: GigaChat smoke (Increment 2)

- [ ] Task 6: Manual smoke checklist 5–10 tutor scenarios on GigaChat credentials
- [ ] Decide primary vs keep DeepSeek

### Phase 3: GigaChat adapter (Increment 3) — Ask first on deps

- [ ] Task 7: Add `langchain-gigachat` (Ask first) + factory branch
- [ ] Task 8: Auth/credentials env for GigaChat; tests with mocks

## Tasks (Increment 1 detail)

### Task 1: Settings LLM_* + fallbacks

**Description:** Add `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL` to `Settings`. Effective key/model fall back to `OPENAI_*`. Property `llm_configured` = chat key present.

**Acceptance criteria:**
- [ ] `LLM_API_KEY` wins over `OPENAI_API_KEY`
- [ ] Empty `LLM_API_KEY` → use `OPENAI_API_KEY`
- [ ] Same for model when using openai key fallback
- [ ] DeepSeek default model `deepseek-chat`; base URL default `https://api.deepseek.com` when provider=deepseek and base empty

**Verification:** unit tests in `tests/tutor/test_llm_provider.py`

**Dependencies:** None  
**Estimated scope:** S (config + tests)

**Files:** `backend/app/core/config.py`, `backend/tests/tutor/test_llm_provider.py`

---

### Task 2: Factory build_chat_llm

**Description:** New module with `build_chat_llm(settings)`. deepseek/openai → `ChatOpenAI` + base_url; gigachat → clear error; unknown → ValueError.

**Acceptance criteria:**
- [ ] deepseek builds ChatOpenAI with expected base_url/model
- [ ] gigachat raises typed/clear error (mapped to 503 by service)
- [ ] No new pip deps; `parallel_tool_calls=False` stays in graph bind

**Verification:** factory unit tests  
**Dependencies:** Task 1  
**Estimated scope:** S

**Files:** `backend/app/services/tutor/llm.py`, tests

---

### Task 3: Wire graph + service + health

**Description:** Replace local `_build_llm` in graph; tutor_service key checks use `llm_configured` / factory error → 503; health adds `llm_configured`, keeps `openai_configured` alias.

**Acceptance criteria:**
- [ ] 503 without effective key (no orphan user msg)
- [ ] 503 when provider=gigachat before adapter
- [ ] Health JSON has both flags, equal values

**Verification:** `pytest tests/tutor/test_tutor_api.py -q`  
**Dependencies:** Task 2  
**Estimated scope:** M

**Files:** `graph.py`, `tutor_service.py`, `schemas/tutor.py`

---

### Task 4: .env.example + frontend soft text

**Description:** Document `LLM_*` (DeepSeek primary, GigaChat next). UI: «LLM API key…» instead of OPENAI_API_KEY. Types: add `llm_configured`.

**Acceptance criteria:**
- [ ] `.env.example` documents DeepSeek defaults + GigaChat next
- [ ] Overlay warning uses neutral wording; vitest updated

**Dependencies:** Task 3  
**Estimated scope:** S

**Files:** `backend/.env.example`, `TutorChatOverlay.tsx`, `tutor.ts`, tests

---

### Task 5: BaseChatModel types (light)

**Description:** Prefer `BaseChatModel` over `ChatOpenAI` in `llm_utils` / solve node signatures where easy — no huge refactor.

**Acceptance criteria:**
- [ ] `invoke_llm` accepts BaseChatModel
- [ ] graph/solve signatures loosened where touched
- [ ] Embeddings / query_rewrite / index_rag untouched

**Dependencies:** Task 3  
**Estimated scope:** S

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| DeepSeek tool-calling quirks | Med | Manual smoke; keep parallel_tool_calls=False |
| Breaking RAG that reads openai_api_key | High | Do not change embeddings path; keep openai_* fields |
| Accidental commit of .env secrets | High | Never touch backend/.env; never print keys |

## Open Questions

None remaining for increment 1 (Q1–Q3 resolved in spec).

## Out of scope this session

- GigaChat adapter / `langchain-gigachat`
- Embeddings → DeepSeek
- Removing `OPENAI_*` fields
- Commit / push
