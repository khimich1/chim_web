# Spec: LLM-провайдер (DeepSeek → GigaChat)

**Версия:** 0.1.1 
**Дата:** 2026-07-25 
**Статус:** approved 
**Источник:** [`docs/ideas/llm-provider-gigachat-deepseek.md`](../ideas/llm-provider-gigachat-deepseek.md)  
**Родитель:** [`tutor-rag.md`](tutor-rag.md) §8, [`SPEC.md`](../../SPEC.md) §1.6 / §12 (AI-советчик)  
**План:** [`tasks/llm-provider.md`](../../tasks/llm-provider.md) 
**Вне scope явно:** hybrid RAG / embeddings / pgvector (другой разработчик)

---

## Assumptions (accepted)

Приняты (ревью человека, 2026-07-25):

1. **Env:** канон — `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`.  
   Legacy `OPENAI_API_KEY` / `OPENAI_MODEL` остаются **алиасами**: если `LLM_API_KEY` пуст, берём `OPENAI_API_KEY` (и аналогично для model). Так не ломаем существующие `.env` и RAG-код, который пока читает `openai_*`.
2. **Один active provider** в рантайме. Нет dual-fallback «DeepSeek упал → GigaChat» в MVP.
3. **MVP implement = DeepSeek (OpenAI-compat) + фабрика.** Адаптер `gigachat` — **следующий инкремент** (контракт/ветка в фабрике: явная ошибка → 503 на request; app стартует).
4. **Health API:** добавить `llm_configured: bool`. Поле `openai_configured` **сохранить** с тем же значением (deprecated alias). UI-текст: нейтральный «LLM API key…» (Q1 — да, в инкременте 1).
5. **Embeddings / hybrid RAG не переключаем** на DeepSeek/GigaChat в этой фиче. `get_embeddings_provider` и `index_rag` продолжают опираться на текущий `openai_api_key` / embedding model; без ключа embeddings — keyword-only как сейчас.
6. **Off-topic / лишние LLM-вызовы** в MVP **не отключаем** ради экономии $15 — отдельное решение при необходимости.
7. **`parallel_tool_calls=False`** остаётся (совместимость с будущим GigaChat).
8. **Новых pip-зависимостей в MVP нет** (DeepSeek через существующий `langchain-openai` + `base_url`). Пакет `langchain-gigachat` — только в инкременте GigaChat (**Ask first**).
9. **Дефолты при `LLM_PROVIDER=deepseek`:**  
 `LLM_BASE_URL=https://api.deepseek.com` (без `/v1` — `langchain-openai` принимает этот host), 
 `LLM_MODEL=deepseek-chat`.
10. **Smoke GigaChat** — ручной чеклист после оживления DeepSeek; не блокер merge инкремента 1.
11. Несколько ключей (DeepSeek + GigaChat) в `.env` одновременно — OK; active выбирается через `LLM_PROVIDER`.
12. Не удалять существующие `OPENAI_*` / другие ключи при добавлении `LLM_*`.

---

## 1. Objective

### Что строим

Тонкую абстракцию LLM-провайдера для AI-репетитора: сейчас **DeepSeek** как OpenAI-compatible endpoint, контракт готов под **GigaChat** без второго большого рефактора.

### Зачем

Нет рабочего OpenAI-ключа. Tutor должен отвечать до/на раннем проде. $15 на DeepSeek — мост; бесплатные токены GigaChat — вероятный следующий primary. Жёсткая привязка к `ChatOpenAI`+OpenAI host мешает обоим сценариям.

### Для кого

| Роль | Эффект |
|------|--------|
| **Ученик / преподаватель** | Tutor снова отвечает (чат, tools, streaming) |
| **Разработчик** | Смена вендора ≈ env + адаптер в одном модуле |
| **RAG-разработчик** | Не затронут этим срезом (embeddings как были) |

### User stories + acceptance

| ID | Story | Acceptance |
|----|--------|------------|
| US-LLM-1 | Как ops, задаю DeepSeek ключ в `.env` и tutor работает | При `LLM_PROVIDER=deepseek` + ключе: health `llm_configured=true`; `send_message` не 503 из‑за отсутствия ключа |
| US-LLM-2 | Как разработчик, граф не знает вендора | `graph` / solve / critic / guards получают LLM из фабрики; нет размазанных `base_url` по файлам |
| US-LLM-3 | Как разработчик, тесты без реального LLM | `pytest` tutor зелёный с mock/injected LLM; реальный API не вызывается |
| US-LLM-4 | Как пользователь, без ключа — понятная ошибка | 503 до персистенции user-msg; orphan messages нет (как сейчас для OpenAI) |
| US-LLM-5 | Как разработчик, путь к GigaChat ясен | В фабрике есть явное место под `gigachat`; в spec/`.env.example` задокументировано «next» |

---

## 2. Tech Stack

| Слой | Стек |
|------|------|
| Backend | FastAPI, pydantic-settings, LangChain / LangGraph, `langchain-openai` (`ChatOpenAI`) |
| DeepSeek | OpenAI-compatible HTTP API (`base_url` + API key) |
| GigaChat (later) | `langchain-gigachat` — **не в MVP** |
| Frontend | Health flag + нейтральный текст про LLM API key |
| Tests | pytest + mock LLM (существующий паттерн tutor tests) |

---

## 3. Commands

```bash
# Backend
cd backend
pytest tests/tutor/ -q
pytest tests/tutor/test_tutor_api.py -q
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Ручной smoke (после ключа в backend/.env)
# 1) GET /api/tutor/health → llm_configured true
# 2) Чат: вопрос по теме учебника
# 3) «Разбери задание N» (solve path)
# 4) Off-topic сообщение → guard
```

---

## 4. Project Structure

```
backend/app/core/config.py              # LLM_* (+ legacy OPENAI_* aliases)
backend/app/services/tutor/llm.py       # NEW: build_chat_llm(settings) factory
backend/app/services/tutor/graph.py     # использовать factory вместо локального ChatOpenAI(...)
backend/app/services/tutor/llm_utils.py # типы: BaseChatModel / protocol, не жёсткий ChatOpenAI где возможно
backend/app/services/tutor_service.py   # проверка ключа через settings.llm_configured helper
backend/app/schemas/tutor.py            # TutorHealthResponse: llm_configured (+ openai_configured alias)
frontend/lib/api/tutor.ts               # типы health (если меняем контракт)
frontend/components/tutor/... # текст про LLM API key
.env.example                            # LLM_* + комментарий DeepSeek / future GigaChat
docs/specs/tutor-rag.md §8              # ссылка на эту спеку + кандидаты
docs/ideas/llm-provider-gigachat-deepseek.md  # статус → spec
```

Файлы embeddings / `index_rag` / hybrid retriever — **не менять** в MVP (кроме случая, когда общий helper «есть ли chat key» случайно сломает их — тогда сохранить чтение `openai_api_key` для embeddings).

---

## 5. Code Style

Канон — одна фабрика:

```python
# backend/app/services/tutor/llm.py
def build_chat_llm(settings: Settings) -> BaseChatModel:
    provider = settings.llm_provider  # "deepseek" | "openai" | "gigachat" | ...
    if provider in ("deepseek", "openai"):
        return ChatOpenAI(
 model=settings.effective_llm_model,
 api_key=SecretStr(settings.effective_llm_api_key) if settings.effective_llm_api_key else None,
 base_url=settings.effective_llm_base_url or None,
            temperature=0,
        )
    if provider == "gigachat":
 raise LlmProviderNotConfigured("GigaChat adapter — next increment")
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
```

Settings (идея):

```python
llm_provider: str = Field(default="deepseek", alias="LLM_PROVIDER")
llm_api_key: str = Field(default="", alias="LLM_API_KEY")
llm_model: str = Field(default="deepseek-chat", alias="LLM_MODEL")
llm_base_url: str = Field(default="", alias="LLM_BASE_URL")
# openai_api_key / openai_model — legacy; effective_* = LLM or OPENAI
# llm_configured: bool property — chat key present for active provider path
```

Именование: `build_chat_llm`, `llm_configured` (property), не размазывать vendor strings по graph nodes.

---

## 6. Testing Strategy

| Уровень | Что |
|---------|-----|
| Unit | Фабрика: `deepseek` → `ChatOpenAI` с ожидаемым `base_url`; unknown provider → error; gigachat → `LlmProviderNotConfigured` |
| Unit | Settings: `LLM_API_KEY` побеждает; fallback на `OPENAI_API_KEY` |
| Integration | Существующие `test_tutor_api.py`: 503 без ключа; mock LLM path зелёный |
| Prove-It | `llm_configured` в health; `openai_configured` всё ещё присутствует и равен ему |
| Manual | Smoke US-LLM-1 сценарии на реальном DeepSeek (не в CI) |

**Не вызывать** реальный DeepSeek/GigaChat в `pytest` по умолчанию.

Coverage: не расширяем % ради этой фичи; новые тесты — точечно на factory + health.

---

## 7. Boundaries

**Always**
- Ключи только в backend `.env` / secrets; не в frontend, не в git
- Mock LLM в pytest
- Проверка «ключ есть» **до** персистенции user-сообщения (сохранить I3 из tutor-rag)
- `parallel_tool_calls=False`

**Ask first**
- Добавление `langchain-gigachat` / любых новых LLM SDK
- Смена embedding-провайдера или переиндексация pgvector
- Удаление полей `openai_*` / `openai_configured` без deprecation window
- LiteLLM или другой proxy-слой
- Отключение guard/off-topic ради экономии токенов

**Never**
- Коммит API keys
- Вызов LLM с frontend
- Ломать keyword-only tutor path при отсутствии embedding key
- Включать parallel tool calls «для скорости»

---

## 8. API / Config contract

### Env (`.env.example`)

```env
# Tutor chat LLM (v2+)
LLM_PROVIDER=deepseek          # deepseek | openai | gigachat (later)
LLM_API_KEY=                   # DeepSeek key now; GigaChat credentials later
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com

# Legacy aliases (optional if LLM_* set)
# OPENAI_API_KEY=
# OPENAI_MODEL=gpt-4o-mini
```

### Health

```json
{
  "rag_index_exists": true,
  "llm_configured": true,
  "openai_configured": true
}
```

`openai_configured` == `llm_configured` в MVP (alias).

### Errors

| Ситуация | Поведение |
|----------|-----------|
| Нет ключа | 503, detail про LLM API key (без утечки stack); user-msg не в БД |
| `LLM_PROVIDER=gigachat` до адаптера | **503 на request** с явным «GigaChat ещё не подключён»; **app стартует** (Q2) |
| Таймаут LLM | Существующий `TUTOR_INVOKE_TIMEOUT` / 504 — без регрессии |

---

## 9. Success Criteria

- [ ] При валидном DeepSeek key tutor отвечает в UI (чат + хотя бы один tool path)
- [ ] `build_chat_llm` — единственное место создания chat LLM для tutor graph/solve
- [ ] `pytest tests/tutor/` зелёный без реального LLM
- [ ] Health отдаёт `llm_configured`; legacy `openai_configured` не сломан
- [ ] `.env.example` и `tutor-rag.md` §8 обновлены (DeepSeek / GigaChat в кандидатах)
- [ ] Embeddings/RAG-код не переведён на DeepSeek «заодно»
- [ ] Idea one-pager ссылается на эту спеку; статус idea = согласован → spec

---

## 10. Phased delivery (для PLAN)

| Инкремент | Содержание | Verify |
|-----------|------------|--------|
| **1** | Settings `LLM_*` + aliases; `build_chat_llm` (deepseek/openai); wire graph/service; health `llm_configured`; UI text; `.env.example`; tests | pytest tutor + ручной DeepSeek smoke |
| **2** | Ручной smoke GigaChat (вне кода или spike-скрипт) → решение primary | Чеклист 5–10 сценариев |
| **3** | `LLM_PROVIDER=gigachat` адаптер (`langchain-gigachat`) | Отдельный PR; Ask first на dependency |

---

## 11. Out of scope / Not Doing

- Hybrid RAG, смена embedding model, reindex
- LiteLLM
- Runtime multi-provider failover
- Переписывание system prompts под вендора
- OpenRouter / Ollama в MVP (остаются кандидатами в §8 tutor-rag, без реализации)
- Удаление `OPENAI_*` в том же PR

---

## 12. Resolved questions

1. **UI-текст (Q1):** да — заменить «OPENAI_API_KEY…» на нейтральный «LLM API key…» в `TutorChatOverlay` + тест.
2. **GigaChat до адаптера (Q2):** `LLM_PROVIDER=gigachat` → app стартует; на request — 503 с понятным текстом (не отказ при import/startup).
3. **BASE_URL / model (Q3):** дефолты `deepseek-chat` и `https://api.deepseek.com` (без `/v1`, если `langchain-openai` не требует).

---

## 13. Связь с tutor-rag.md

Эта спека **уточняет и реализует** §8 `tutor-rag.md`. При конфликте по chat-LLM provider — приоритет у этого документа до merge; embeddings/RAG по-прежнему у `tutor-rag.md` + ADR-002.
