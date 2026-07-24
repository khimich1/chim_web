# LLM-провайдер: DeepSeek сейчас → GigaChat потом

**Проект:** `chim_web`  
**Дата:** 2026-07-23  
**Статус:** idea-refine согласован (направление C) → **spec:** [`../specs/llm-provider.md`](../specs/llm-provider.md)  
**Связанные артефакты:**
- [`../specs/llm-provider.md`](../specs/llm-provider.md) — **spec (фаза SPECIFY)**
- [`../specs/tutor-rag.md`](../specs/tutor-rag.md) §8 — абстракция `LlmProvider` / `LLM_PROVIDER` (обновлено)
- `backend/app/services/tutor/graph.py` — сейчас жёстко `ChatOpenAI`
- `backend/app/core/config.py` — `OPENAI_API_KEY` / `OPENAI_MODEL`
- Embeddings / hybrid RAG — **вне scope** (другой разработчик)

---

## Problem Statement

**How Might We** оживить AI-репетитора (чат + tool-calling + streaming) без OpenAI-ключа — так, чтобы сейчас быстро работать на DeepSeek ($15), а позже перейти на GigaChat (бесплатные токены, русский) без второго большого рефактора?

---

## Recommended Direction

**C: DeepSeek drop-in сейчас + тонкая провайдерная абстракция под GigaChat.**

1. **Сейчас:** подключить DeepSeek как OpenAI-compatible endpoint (`base_url` + ключ + модель) — минимальный diff к существующему `ChatOpenAI` / LangGraph.
2. **Одновременно:** вынести выбор вендора в settings (`LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, опционально `LLM_BASE_URL`), не размазывая `openai_*` по графу.
3. **Smoke-тест GigaChat (1–2 ч):** 5–10 сценариев tutor (вопрос по теме, «разбери задание N», off-topic). Если tool-calling стабилен — можно сделать GigaChat primary раньше; иначе DeepSeek primary, GigaChat — следующий адаптер.
4. **Потом:** адаптер `langchain-gigachat` за тем же интерфейсом; смена = env + небольшой provider module.

**Почему не A (только DeepSeek):** $15 быстро сгорят на проде (несколько LLM-вызовов на сообщение: agent, guards, solve/critic); путь к GigaChat всё равно нужен.

**Почему не B (сразу только GigaChat):** выше риск на tool-calling/auth; при провале — tutor снова мёртв. Абстракция + DeepSeek как рабочий мост снимает этот риск.

RAG / embeddings / pgvector **не трогаем**: keyword fallback остаётся; hybrid — задача другого разработчика.

---

## Key Assumptions to Validate

- [ ] DeepSeek стабильно отдаёт **tool_calls** в ReAct-графе (`bind_tools`, уже `parallel_tool_calls=False`) — проверить на 5–10 реальных диалогах.
- [ ] Streaming (`invoke_llm` / SSE) работает с DeepSeek без поломки UX.
- [ ] Без нового RAG tutor полезен для раннего прода (keyword + tools достаточно).
- [ ] GigaChat tool-calling на этом же графе приемлем (smoke до выбора primary надолго) — иначе GigaChat остаётся «следующим адаптером», не блокером MVP.
- [ ] Расход DeepSeek $15 хватит до появления GigaChat-адаптера (или лимиты/кэш вызовов не убьют бюджет за дни).

---

## MVP Scope

**В scope**
- Env: `LLM_PROVIDER=deepseek` (или `openai`-совместимый), `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL=https://api.deepseek.com`
- Фабрика LLM в одном месте (`_build_llm` / будущий provider), чтобы graph/solve/critic/guards не знали про вендора
- Обновить `.env.example`, health/`openai_configured` → нейтральный флаг вроде `llm_configured`
- Ручной smoke: чат tutor + один solve-сценарий + off-topic guard
- Документировать: DeepSeek primary сейчас; GigaChat — next adapter

**Вне scope (Not Doing ниже)**
- Hybrid RAG / смена embeddings
- Полноценный GigaChat-адаптер в том же PR (только контракт, чтобы его было куда воткнуть)
- OpenRouter / Ollama (пока не нужны)
- Переписывание промптов «под вендора»

---

## Not Doing (and Why)

- **Сразу только GigaChat без моста** — риск сломать tool-calling на проде; нет запасного рабочего ключа в том же паттерне API.
- **DeepSeek «навсегда» без абстракции** — гарантированный второй рефактор при переходе на GigaChat.
- **DeepSeek chat + GigaChat embeddings сейчас** — RAG не в этой задаче; два вендора без нужды.
- **Трогать hybrid RAG / pgvector / index_rag** — чужой трек; keyword fallback уже есть.
- **LiteLLM как dependency в MVP** — overkill; достаточно тонкой фабрики + OpenAI-compat для DeepSeek.
- **Параллельный tool-calling** — GigaChat не поддерживает; в коде уже `parallel_tool_calls=False`, не включать.

---

## Open Questions

- Имена env: сохранить алиасы `OPENAI_*` для совместимости или сразу `LLM_*` (spec §8)?
- Нужен ли DeepSeek как fallback после переключения на GigaChat, или только один active provider?
- Когда smoke GigaChat: до merge DeepSeek-моста или сразу после оживления tutor?
- Стоит ли временно отключить/урезать дорогие LLM-вызовы (off-topic checker на каждое сообщение) пока на $15?

---

## Suggested next step

Спека: [`../specs/llm-provider.md`](../specs/llm-provider.md) — **ждёт ревью Assumptions**.  
После approve → PLAN / tasks → инкремент 1 (DeepSeek + `LLM_*` factory).
