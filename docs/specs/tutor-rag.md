# Spec: AI-советчик (Agent + RAG)

**Версия:** 0.8.2  
**Дата:** 2026-06-09 (обновлено 2026-06-18)  
**Фаза:** v2+ (после MVP)  
**Родитель:** [`SPEC.md`](../../SPEC.md) §1.6, US-6  
**Статус:** черновик по результатам ревью

---

## 1. Objective

### Что строим

Чат-помощник по химии для учеников и преподавателей репетиторского приложения `chim_web`.

| Компонент | Роль |
|-----------|------|
| **RAG (Retrieval)** | Находит релевантные фрагменты в подготовленном контенте |
| **Agent (LangGraph ReAct)** | Оркестрирует tools, формирует ответ с цитатами, отклоняет off-topic |

### Зачем

- Ответы **на основе учебника** репетитора, а не общих знаний LLM.
- Единая точка вопросов по теории рядом с тестами и ДЗ.
- Преподаватель видит, о чём спрашивают ученики.

### Для кого

| Роль | Возможности |
|------|-------------|
| **Ученик** | Глобальный чат; продолжение сессии; ссылки на источники |
| **Преподаватель** | Свой чат + просмотр истории диалогов своих учеников |

### Вне scope (этой spec)

- AI-проверка письменных заданий (`grading_mode: ai_assisted`) — отдельная фича v2.
- Голосовой ввод/озвучка ответов.
- Редактирование контента учебника через чат.

---

## 2. Источники данных для RAG

Контентные SQLite — **read-only** (как в MVP). Индекс строится **offline**.

| Источник | Таблица | Индексируемые поля | `source` |
|----------|---------|-------------------|----------|
| Учебник | `prepared_lectures` | `topic`, `chunk_idx`, `chunk_title`, `lecture` | `lecture` |
| Самопроверка | `prepared_lectures` | `qa_questions`, `qa_answers` (JSON → отдельные doc на пару Q/A) | `lecture_qa` |

**Не индексировать:** `correct_ans`, `tts_audio`, BLOB, **`tests.hint`, `tests.detailed_explanation`**.

> **РЕШЕНО (2026-06-17) — RAG только по учебнику.** Готовые разборы из банка тестов
> (`hint`, `detailed_explanation`) в индекс **не попадают** — возврат к философии `RAG_chemistry`:
> агент строит разбор **сам** от теории учебника + сверки с `correct_ans` (solve-pipeline, §17),
> а не копирует готовый текст. Это (1) убирает «формальный RAG» (ответ из чужого разбора вместо
> теории), (2) исключает риск утечки разбора задания во время теста, (3) делает источники ответов
> однородными (всегда учебник, всегда кликабельная цитата `topic/chunk_title`). Текущий
> `ingest_test_documents` из ingestion-пайплайна советчика **удаляется** (см. Task 41 в плане).

### Формат документа для индекса

```text
source: lecture
topic: Алканы
chunk_idx: 2
chunk_title: Реакции горения
---
{lecture markdown}
```

```text
source: lecture_qa
topic: Алканы
chunk_idx: 2
chunk_title: Реакции горения
field: question
---
Вопрос: ... / Ответ: ...
```

### Метаданные (для фильтрации retrieval)

```python
class RagDocumentMeta(TypedDict, total=False):
    source: Literal["lecture", "lecture_qa"]   # test-источник удалён (см. §2 РЕШЕНО)
    topic: str
    chunk_idx: int
    chunk_title: str
    track: Literal["ege", "oge"]               # для lecture/lecture_qa — track-agnostic
    field: Literal["question", "answer"]       # только для lecture_qa
```

---

## 3. Архитектура

```
Frontend (TutorChat)
       │ POST /api/tutor/sessions/{id}/messages
       ▼
TutorRouter → TutorService
       │
       ├── TutorSessionRepo (PostgreSQL) — история
       ├── AgentGraph (LangGraph ReAct)
       │        │
       │        └── Tools ──→ RagRetriever ──→ vector/keyword store
       │                 └── LectureContentRepo / ExamContentRepo (read)
       └── LlmProvider (абстракция)
```

### Слои backend

```
backend/app/
├── api/routers/tutor.py
├── schemas/tutor.py
├── services/
│   ├── rag/
│   │   ├── indexer.py      # CLI: python -m app.cli.index_rag
│   │   ├── retriever.py    # search(query, filters) -> list[ChunkHit]
│   │   └── store.py        # pgvector / keyword index
│   └── tutor/
│       ├── agent.py        # build_graph(), invoke()
│       ├── tools.py        # @tool retrieve_theory, get_task, search_tasks, ...
│       ├── prompts.py      # STUDENT_SYSTEM, TEACHER_SYSTEM
│       └── guards.py       # is_on_topic, sanitize_tool_output
├── repositories/
│   ├── content/            # существующий read-only слой
│   └── app/tutor.py        # TutorSession, TutorMessage
└── models/tutor.py
```

### Agent tools (v2+ MVP срез)

| Tool | Описание | Доступ |
|------|----------|--------|
| `retrieve_theory` | RAG по **учебнику** (`lecture`, `lecture_qa`); возвращает hits с `topic`, `chunk_idx`, `chunk_title` | student, teacher |
| `get_task` | Текст задания + `correct_ans` для разбора (**только вне** активной тест-сессии ученика) | student, teacher |
| `search_tasks` | Поиск заданий в банке по подстроке/`type` (без `correct_ans` в preview) | student, teacher |
| `save_user_info` | Профиль ученика (`name`, `grade`, `weak_topics`, …) | student |

> **Удалено (v0.8.1):** `get_test_explanation` — `hint`/`detailed_explanation` **не** индексируются и **не** отдаются через RAG-tool (§2). Разбор задания — solve-pipeline (§17): `get_task` + `retrieve_theory` + сверка ключа в коде.

**Запрещённые данные в tools/prompt:** `correct_ans` во время активной тест-сессии ученика; сырые ответы других учеников; готовые test-разборы как источник цитат.

### LangGraph (паттерн)

По образцу учебного `airline_react_agent.py`:

```
START → input_guard → agent ⇄ ToolNode → tool_output_guard → agent → END
```

- `parallel_tool_calls=False` — один tool за шаг.
- System prompt: «для теории — `retrieve_theory`; разбор задания — `get_task` + теория; не выдумывай; цитируй `topic`/`chunk_title` из учебника».

---

## 4. Retrieval strategy

### Целевой retrieval (РЕШЕНО 2026-06-17) — hybrid на pgvector

| Срез | Реализация | Статус | Критерий готовности |
|------|------------|--------|---------------------|
| **2a** | Keyword/BM25 (`keyword_score` по title+body, RU stop-words) | ✅ реализован | 10 эталонных вопросов → top-3 содержит ожидаемый чанк |
| **2b** | **Hybrid: keyword ∪ vector, rerank top-10 → top-4** | 🎯 **целевой, приоритет №1** | recall@5 ≥ 0.8 на eval-наборе; кейс «химические свойства карбоновых кислот» находит чанк `[2]` |

**Решение (закрыто):**

- **Hybrid, не «или-или».** Семантический слой добавляется **поверх** keyword (объединение кандидатов + rerank top-10 → top-4), а не заменяет его. Keyword хорош на точных терминах/формулах, embeddings — на синонимах и перефразировании. Это и есть «лучшее из `RAG_chemistry`» (там retrieval был чисто семантический) плюс уже работающий keyword.
- **Хранилище embeddings — `pgvector`** в существующем PostgreSQL (одна БД, prod-friendly, транзакционно с app-данными). **Chroma** (`vectorstore.py`/`chroma_ingestion.py`) остаётся dev-заготовкой/фолбэком, в проде советчика **не используется**. ADR фиксирует выбор pgvector.
- **Embeddings-модель** — OpenAI `text-embedding-3-small` (как в `RAG_chemistry`), ключ из `.env`; индексация **offline** (CLI), в рантайме эмбеддится только запрос.
- **`Retriever.search()` сигнатура не меняется** — hybrid включается настройкой (`rag_hybrid_enabled`), keyword-only остаётся фолбэком при отсутствии `OPENAI_API_KEY`/индекса.

**CLI индексации:**

```bash
cd backend
python -m app.cli.index_rag --rebuild          # keyword-индекс (rag_index.json)
python -m app.cli.index_rag --embeddings       # векторный индекс в pgvector (нужен OPENAI_API_KEY)
```

### ⚠️ Текущее состояние (2026-06-17) — главный пробел точности

> `retrieve_theory` сейчас использует **только keyword/BM25** (`search_theory` → `Retriever` →
> `keyword_score`). Векторный слой (`vectorstore.py`, `embeddings.py`, `chroma_ingestion.py`)
> **портирован, но НЕ подключён** к поиску советчика. То есть мы **отошли** от `RAG_chemistry`,
> где retrieval **семантический** (Chroma + `text-embedding-3-small`).

**Последствие (реальный кейс).** На запрос «химические свойства карбоновых кислот» keyword-поиск
вытащил чанк `[1] Свойства и изомерия карбоновых кислот` (слово «свойства» в заголовке + ×2 буст
title), хотя ответ — в чанке `[2] Карбоновые кислоты: свойства и получение` (раздел «### Химические
свойства карбоновых кислот»). Контент в учебнике **есть**, но keyword-ранжирование промахнулось →
агент честно ответил «в фрагментах нет», сослался не на тот раздел.

**Вывод:** повышение точности retrieval — приоритет №1; целевое решение — hybrid на pgvector (выше).
Реализация — **Task 41** в `tasks/plan.md` (срез 16-1, ведущая задача точности).

### Использование `page_context.topic` (РЕШЕНО — НЕ используем)

Overlay передаёт тему открытой страницы в `page_context.topic`, но retrieval её **намеренно игнорирует**
(используется только `test_session_id` для gating). Решение (2026-06-17): **не** пробрасывать
`page_context.topic` в `retrieve_theory`. Причины: (1) ученик часто спрашивает не по текущей странице;
жёсткая привязка/буст темы исказит поиск; (2) hybrid retrieval сам должен находить нужный чанк по смыслу —
это правильное место для усилий, а не топик-фильтр-костыль. Поиск остаётся **по всему учебнику** в рамках
трека ученика. (Можно вернуться к идее как к необязательному UX-бусту после оценки hybrid на eval-наборе.)

### Адаптация запроса под учебник (query rewriting) — РЕШЕНО 2026-06-18

> **Проблема (реальный кейс).** На вопрос «как с металлами реагирует сера?» keyword/hybrid
> retrieval часто поднимает чанки про **металлы + кислоты/соли** (общее слово «металлы»),
> хотя ответ есть в учебнике (`Cера` → «Получение и свойства сероводорода»: `S + Cu = CuS`,
> `S + Ca = CaS`). Агент честно отвечает «не нашёл в учебнике», потому что в **найденных**
> фрагментах нет ответа. Корневая причина — не отсутствие контента, а **несовпадение
> формулировки ученика с терминологией учебника** и нестабильный `query`, который ReAct-агент
> передаёт в `retrieve_theory`.

**Решение:** явный шаг **адаптации запроса до `Retriever.search()`**, а не только надежда
на то, что LLM в tool-call подберёт удачную строку поиска.

```
Вопрос ученика (+ опц. page_context.topic)
        │
        ▼
  Query rewriter ──► 1–3 поисковых запроса (термины учебника)
        │
        ▼
  Multi-query retrieval (каждый query → hybrid search)
        │
        ▼
  Merge + dedup + rerank (A5) → top_k фрагментов → ответ агента
```

| Компонент | Описание |
|-----------|----------|
| **Query rewriter** | Короткий LLM-вызов или rule-based препроцессор: из вопроса школьника — 1–3 строки для BM25/embeddings с **именами веществ, типами реакций, формулами** из программы. Пример: «как с металлами реагирует сера?» → `сера металлы сульфиды`, `S Cu CuS CaS`, `реакции серы с металлами`. |
| **Multi-query** | Каждый вариант ищется отдельно; результаты объединяются (union) перед dedup/rerank. Снижает риск одного неудачного query. |
| **Мягкий сигнал `page_context.topic`** | **Не** жёсткий фильтр `topic=` (см. решение выше). Опционально: rewriter добавляет название темы страницы **в один из** search-queries или как буст при rerank — только если вопрос явно про текущую тему. Жёсткий `topic`-фильтр не делаем по умолчанию. |
| **Где в коде** | Предпочтительно **внутри** `retrieve_theory` / `search_theory` (прозрачно для графа) или отдельный узел `rewrite_query` **перед** `ToolNode` (если нужен лог отдельного шага). Фичефлаг `rag_query_rewrite_enabled`. |
| **Eval** | Добавить в `tests/tutor/eval/`: «как с металлами реагирует сера?» → `topic: Cера`, `chunk_idx: 1`; recall@5 после rewriter ≥ порога набора. |

**Связь с другими улучшениями:**

- **A4 (hybrid)** — ловит синонимы, но не спасает, если query утащил поиск в другую тему («металлы» без «серы»).
- **A3 (порог)** — отложен; rewriter снижает ложные «не нашёл» при непустом индексе.
- **U3 (suggested prompts)** — UX-подсказки ученику; rewriter — серверная адаптация без участия пользователя.

**Порядок:** после **A4 + A5 + eval (O2)** — срез **16-1b** / Task **41.4** в плане.

---

## 5. API

### POST `/api/tutor/sessions`

Создать сессию. Role: `student` | `teacher`.

```json
{
  "page_context": {
    "topic": "Алканы",
    "test_session_id": null,
    "homework_id": null
  }
}
```

### POST `/api/tutor/sessions/{id}/messages`

```json
{
  "content": "Почему алканы малореакционны?"
}
```

**Поведение `TutorService.send_message`:**

1. Проверить доступность LLM (`OPENAI_API_KEY` или injected mock) **до** персистенции user-сообщения.
2. Сохранить user-сообщение.
3. Вызвать LangGraph (`graph.invoke`) в **отдельном потоке** (`asyncio.to_thread`) — sync LLM/RAG не блокирует event loop.
4. Сохранить assistant-сообщение + `sources`; commit.
5. При ошибке агента — `rollback`, user-сообщение не остаётся в БД; клиенту `503` с понятным `detail`.

**Нефункциональные требования:**

| Требование | Реализация |
|------------|------------|
| Не блокировать event loop | `asyncio.to_thread(graph.invoke, …)` |
| Не держать DB-транзакцию на время LLM | commit user-msg → invoke → commit assistant (или отдельная сессия) |
| Таймаут вызова агента | `asyncio.wait_for(to_thread(...), timeout=…)` — configurable в settings |
| Сериализация JSON в БД | `model_dump(mode="json")` для `page_context`, `sources` |

**Response:**

```json
{
  "message_id": "uuid",
  "role": "assistant",
  "content": "...",
  "sources": [
    {
      "source": "lecture",
      "topic": "Алканы",
      "chunk_idx": 1,
      "chunk_title": "Свойства алканов"
    }
  ]
}
```

### GET `/api/tutor/students/{student_id}/sessions`

Teacher only; RBAC: только свои ученики.

---

## 6. UI

| Экран | Роль | Приоритет |
|-------|------|-----------|
| Плавающее окно (overlay-панель) поверх учебника и тестов | student | P2 |
| Список сессий ученика + transcript | teacher | P2 |

**UX (overlay):**

- Чат — **не отдельная страница**, а плавающая панель (drawer/floating window), вызываемая кнопкой с любого экрана кабинета (поверх учебника и тестов).
- Окно не перекрывает прохождение теста: сворачивается/перетаскивается; состояние сессии сохраняется при сворачивании.
- Контекст текущей страницы (тема лекции, активный тест) автоматически кладётся в `page_context`.
- Показ `sources` как кликабельные ссылки: «Алканы → Свойства алканов».
- Индикатор «ищу в учебнике…» на время tool-вызовов (при отправке сообщения).
- Индикатор загрузки при **первом открытии** overlay (health + создание/загрузка сессии).
- `aria-live="polite"` на индикаторе загрузки (a11y).
- Markdown в ответах с sanitization.
- Кнопка открытия чата **disabled** на время `handleOpen` (защита от двойного клика).

### Жизненный цикл `page_context` (overlay)

- При **создании** сессии `page_context` сериализуется в JSON (`model_dump(mode="json")`) — UUID → string.
- При **смене маршрута** (`pathname`) overlay должен либо:
  - создать **новую** сессию с актуальным `page_context`, либо
  - обновить `page_context` существующей сессии (PATCH, если добавим endpoint).
- Текущая реализация кэширует `sessionId` в React state — при навигации учебник → тест контекст **устаревает**; это баг, см. §15.

---

## 7. Persistence (PostgreSQL)

```sql
-- концептуально
tutor_sessions (id, user_id, role_context, page_context jsonb, created_at, updated_at)
tutor_messages (id, session_id, role, content, sources jsonb, created_at)
rag_embeddings (id, doc_id, source, metadata jsonb, embedding vector)  -- срез 2b
```

История **не** в LangGraph MemorySaver как единственное хранилище — checkpointer опционален; source of truth — PostgreSQL.

> ✅ **Реализовано (Task 38, B1):** граф компилируется **без** checkpointer (stateless),
> а multi-turn контекст реплеится из PostgreSQL (`TutorRepository.list_messages` →
> `TutorService._history_to_lc_messages`). In-memory `MemorySaver` удалён, поэтому
> история переживает рестарт и работает при нескольких uvicorn-воркерах.

---

## 8. LLM provider

**Решение:** абстракция до выбора vendor.

```python
class LlmProvider(Protocol):
    def chat(self, messages: list[Message], tools: list[Tool] | None = None) -> AiMessage: ...
```

Кандидаты: OpenAI, OpenRouter, Ollama. Выбор — см. `SPEC.md` §12.7.

Env:

```env
LLM_PROVIDER=openai   # openai | openrouter | ollama
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=...
```

---

## 9. Security & guardrails

| Риск | Митигация |
|------|-----------|
| Галлюцинации | Ответ только после tool; пустой retrieval → отказ |
| Утечка ответов теста | `correct_ans` не в tools/prompt |
| Prompt injection в `lecture` | `tool_output_guard`; strip injection patterns |
| Off-topic | `input_guard` + `is_on_topic` |
| Стоимость API | Без rate limit на v2+ (мало users); логирование токенов |
| RBAC | Teacher видит только своих учеников |

---

## 10. Testing

| Уровень | Что |
|---------|-----|
| Unit | `keyword_score`, `Retriever.search`, tool wrappers (mock DB) |
| Integration | `POST /api/tutor/...` с mock LLM (фиксированные tool_calls) |
| Prove-It | `page_context.test_session_id` (UUID → JSON); 503 без OpenAI key не оставляет orphan user-msg |
| E2E (опционально) | 3 эталонных вопроса с реальным LLM в CI nightly |

**Не вызывать** реальный LLM в `pytest` по умолчанию.

### Регрессионные тесты (code review 2026-06-17)

| Тест | Что ловит |
|------|-----------|
| `test_create_session_serializes_test_session_id_in_page_context` | UUID в `page_context` не сериализуется без `mode="json"` |
| `test_send_message_without_openai_key_returns_503` | ✅ user-msg не персистится при 503 (assert 0 messages) |
| `test_send_message_agent_error_returns_503_and_rolls_back` | ✅ явный rollback при ошибке `graph.invoke` |
| `test_session_transcript_ordered_by_created_at` | ✅ B2: порядок сообщений в transcript |
| `test_tutor_health_requires_auth` | ✅ B4: health не публичный (401 без auth) |
| `test_multi_turn_history_replayed_into_agent` | ✅ B1: история реплеится в граф из PostgreSQL |

---

## 11. Acceptance criteria

- [ ] AC-6.1 … AC-6.6 из `SPEC.md` US-6.
- [ ] Индекс пересобирается CLI без ручных шагов.
- [ ] Retriever: 8/10 эталонных вопросов → ожидаемый чанк в top-3 (срез 2a).
- [ ] Agent trace: минимум один вызов `retrieve_theory` на теоретический вопрос.
- [ ] Teacher не может читать сессии чужих учеников (403).

---

## 12. Open questions (до implement)

1. ~~**Поведение на экране теста**~~ **Решено:** во время активной `TestSession` — только теория; solve-ветка и `correct_ans` отключены (gating). Вне теста разбор заданий доступен.
2. **LLM провайдер** — OpenAI vs OpenRouter vs local.
3. ~~**pgvector vs Chroma**~~ **Решено (§4):** pgvector в PostgreSQL для prod; Chroma — dev-фолбэк.
4. Нужен ли преподавателю **другой** system prompt (методические советы vs объяснение ученику)?

---

## 13. Implementation slices

```
Срез 2a-1: RagRetriever (keyword) + indexer CLI + pytest
Срез 2a-2: tools + agent graph (mock LLM) + TutorService
Срез 2a-3: API + PostgreSQL sessions/messages
Срез 2a-4: Frontend TutorChat (student)
Срез 2a-5: Teacher transcript view
Срез 2b:   embeddings + hybrid retrieval (ADR)
Срез 2c:   Real LLM provider + guardrails hardening
```

После одобрения → задачи в `tasks/plan.md` (Task 31+).

---

## 15. Code review findings (2026-06-17)

> Ревью: `TutorChatOverlay`, `tutor_service.send_message`, `asyncio.to_thread`, обработка ошибок, UX загрузки.  
> **Verdict:** REQUEST CHANGES — нет Critical, есть Important до production.  
> ✅ **Статус (Task 38):** все Important round 1 (I1–I7) и round 2 (B1–B4) + Suggestions
> S1, S3, S4 закрыты. Отложено: **S2** (markdown-рендер в `MessageBubble`) — отдельный
> подсрез; **B-S1/B-S2** (оптимизация `list_sessions`, track преподавателя) — backlog.

### Critical

_Нет._

### Important (до merge / перед real LLM)

| # | Область | Проблема | Требуемое исправление |
|---|---------|----------|----------------------|
| I1 | `TutorChatOverlay` | `sessionId` не сбрасывается при смене `pathname` — агент получает устаревший `page_context` | Сброс `sessionId` при изменении `pageContext` или новая сессия на маршрут |
| I2 | `send_message` | DB-соединение/транзакция удерживается на всё время `graph.invoke` (десятки секунд) | Двухфазный commit: user-msg → invoke вне транзакции → assistant-msg |
| I3 | `send_message` | Проверка `OPENAI_API_KEY` после `flush` user-сообщения | Проверка **до** персистенции; явный `rollback` при 503 (не полагаться только на cleanup `get_db`) |
| I4 | `send_message` | `asyncio.to_thread` без таймаута — зависший LLM блокирует worker thread pool | `asyncio.wait_for(..., timeout=settings.tutor_invoke_timeout)` |
| I5 | `send_message` | При ошибке агента `detail` всегда про `OPENAI_API_KEY`, маскирует другие сбои | Разделить: нет ключа / таймаут / внутренняя ошибка агента |
| I6 | `TutorChatOverlay` | `handleOpen` без loading state и без защиты от double-click | `opening` state, disable кнопки, spinner при загрузке истории |
| I7 | Тесты | `test_send_message_without_openai_key_returns_503` не проверяет отсутствие user-msg в БД | Assert: 0 user messages после 503 |

### Suggestions

| # | Область | Улучшение |
|---|---------|-----------|
| S1 | `TutorChatOverlay` | `aria-live="polite"` на индикаторе «Ищу в учебнике…» |
| S2 | `TutorChatOverlay` | Markdown-рендер ответов + sanitization (spec §6) |
| S3 | `send_message` | `sources`: `model_dump(mode="json")` для единообразия с `page_context` |
| S4 | `TutorChatOverlay` | vitest: overlay open/send/error paths (сейчас только ручная проверка) |

### Round 2 (2026-06-17): обзор всего проекта

> Расширенный проход `code-reviewer` по всему backend tutor-слою
> (`graph.py`, `guards.py`, `tools.py`, `tutor_repo.py`, `tutor_service.py`).
> Gating `correct_ans` во время активной тест-сессии проверен отдельно — **реализован корректно** (`tools.get_task`).

#### Important

| # | Область | Проблема | Требуемое исправление |
|---|---------|----------|----------------------|
| B1 | `memory.get_checkpointer` + `send_message` | Контекст диалога держится только в in-memory `MemorySaver` (`@lru_cache`); история из PostgreSQL **не реплеится** в граф (`invoke_input` = только новое сообщение). При рестарте процесса или нескольких uvicorn-воркерах агент «забывает» диалог, хотя §7 объявляет PostgreSQL source of truth. | Подгружать историю из `TutorRepository` в `invoke_input`, либо персистентный checkpointer (Postgres saver). До этого — prod в **один воркер** + ADR. |
| B2 | `tutor_repo.get_session` | `joinedload(TutorSession.messages)` без `order_by` — порядок сообщений transcript не гарантирован SQL-стандартом. | `order_by(TutorMessage.created_at)` на relationship или в запросе. |
| B3 | `guards.input_guard` | Off-topic классификация только на **первом** сообщении (`has_history = len(messages) > 1`); последующие проходят без проверки → агент уводится после одного on-topic вопроса. | Проверять каждое user-сообщение, либо явно задокументировать trade-off (экономия LLM-вызовов). |
| B4 | `tutor.get_tutor_health` | Endpoint публичный — раскрывает `openai_configured` / `rag_index_exists` без авторизации (info disclosure). | Закрыть под `CurrentUser`. |

#### Suggestions

| # | Область | Улучшение |
|---|---------|-----------|
| B-S1 | `tutor_repo.list_sessions_for_user` | `joinedload` коллекции ради `len(messages)` даёт row-multiplication; на списках — `func.count` подзапросом (при росте числа сообщений). |
| B-S2 | `_build_run_context` | Для teacher `track` всегда `EGE` → теория ищется только по EGE. Уточнить желаемое поведение для преподавателя. |

### Что сделано хорошо

- `asyncio.to_thread` для sync LangGraph — правильный паттерн, event loop не блокируется.
- Optimistic UI в `handleSend` с откатом при ошибке.
- `formatFetchError` + health warning при открытии.
- Prove-It тест UUID в `page_context` (`model_dump(mode="json")` в `create_session`).
- RBAC и mock LLM в `test_tutor_api.py`.

---

## 14. Интеграция готового агента `RAG_chemistry`

**Решение (SPEC §11, допущение 13):** движок советчика — портированный `RAG_chemistry`
(монолит внутри backend), а не разработка с нуля. Источники контента совпадают
(`prepared_lectures.db`, `test_ege.db`, `test_oge.db`), поэтому порт прямой.

### Что переиспользуем как есть

- Топология графа `START → input_guard → agent ⇄ tools → tool_output_guard → agent → END`.
- `retrieve_theory` (RAG по `prepared_lectures`) и guardrails (off-topic, injection в retrieved-тексте).
- Ingestion и формат документов с metadata (`topic`, `chunk_title`, `chunk_idx`). **Векторный слой портируем на pgvector** (а не Chroma — решение §4); Chroma остаётся dev-фолбэком.
- Solve-pipeline v1.5 (planner / solver / critic / `validation.py`) — для разбора заданий **вне теста**.

### Маппинг модулей RAG_chemistry → chim_web/backend

| RAG_chemistry | chim_web/backend | Изменения при порте |
|---------------|------------------|---------------------|
| `services/rag/{ingestion,embeddings,vectorstore,retriever}.py` | `app/services/rag/` | retriever: фильтр `track`; индекс по обоим трекам с `track` в metadata |
| `services/tasks/repository.py`, `services/tasks/validation.py` | `app/services/tutor/tasks.py` поверх существующего `repositories/content/tests.py` | `correct_ans` остаётся серверным, в prompt ученику не утекает |
| `agents/chemistry/{graph,tools,prompts,guardrails}.py` | `app/services/tutor/` | tools получают `user` + `track`; RBAC |
| `agents/chemistry/{planner,solver,critic,task_flow,state}.py` (v1.5) | `app/services/tutor/solve/` | gating: solve-ветка отключается при активной `TestSession` |
| `agents/chemistry/memory.py` (JSON profile + `MemorySaver`) | `repositories/app/tutor.py` (PostgreSQL) | профиль и история — per-user в БД |
| `core/config.py` (свой `Settings`) | слить в `app/core/config.py` | префиксы `LLM_*`, `RAG_*`, `CHROMA_*` |
| `cli.py` | → `api/routers/tutor.py` | CLI остаётся dev-утилитой (опционально) |

### Gating solve-pipeline (по решению владельца)

- **Вне теста:** ученик может «разбери задание N» → детерминированный `prepare_context`
  (`get_task` → `retrieve_theory`) → `solver` → `critic`; финальный ключ сверяется кодом
  с `correct_ans` (`validation.py`). Разбор показывается ученику.
- **Во время активной `TestSession` ученика:** solve-ветка и `get_task` с `correct_ans`
  отключены; доступна только теория (`retrieve_theory`).
- `intent_router` дополнительно проверяет наличие активной тест-сессии для текущего ученика.

### Память и multi-user (отличие от RAG_chemistry)

- `save_user_info` → запись профиля ученика в app DB по `user_id` (вместо `data/user_profile.json`).
- История диалога — `tutor_sessions` / `tutor_messages` (§7); `MemorySaver` опционален как кэш потока.

### Track ЕГЭ/ОГЭ (отличие от RAG_chemistry)

- В `RAG_chemistry` экзамен — глобальная настройка `Settings.exam`.
- В chim_web индекс строится по **обоим** трекам, `track` кладётся в метаданные;
  retriever и task-tools фильтруют по треку текущего ученика.

### UI (overlay)

- Чат — плавающее окно поверх учебника и тестов (см. §6), а не отдельная страница.

### Зависимости (Ask first — security)

Добавляются в `backend/requirements.txt`: `langgraph`, `langchain-core`,
`langchain-openai`, `chromadb` (или `langchain-chroma`). `pydantic-settings` уже есть.
Версии зафиксировать; конфликт с текущим стеком backend проверить при Task 37.

---

## 16. Roadmap: надёжность и расширение агента (v0.6)

> Раздел задаёт направление развития советчика **после** базового среза 2a (Task 38).
> Цель — два независимых трека: **(A) сделать ответы надёжнее** и **(B) расширить то,
> что агент умеет делать внутри продукта**. Все предложения привязаны к уже существующим
> сервисам/моделям (`HomeworkService`, `TestSession`, `GradingService`, `prepared_lectures`).
> Каждая фича — отдельный вертикальный срез (см. `02-incremental-implementation`), за фичефлагом.

### 16.1 Надёжность ответов (приоритет)

Текущая реализация — ReAct v1: качество держится на system prompt и «доброй воле» LLM.
Главные риски: пропуск `retrieve_theory`, ответ без цитаты, расхождение разбора и ключа.

| # | Улучшение | Проблема, которую закрывает | Где | Эффект/Сложность |
|---|-----------|------------------------------|-----|------------------|
| **A1** | **Solve-pipeline v1.5** (детерминированный `prepare_context` → `solver` → `critic` + `validation.py`) для разбора заданий **вне теста** | LLM может не вызвать `get_task`; финальный ключ не сверяется с `correct_ans`; разбор расходится с ответом | новый `services/tutor/solve/` (порт из `RAG_chemistry` §14) | Высокий / Высокая |
| **A2** | **Принудительная цитата** — критик/пост-проверка: ответ по теории обязан содержать `topic`/`chunk_title` из реально вызванного `retrieve_theory`; иначе retry или дисклеймер | «RAG формальный»: tool вызван, но ответ из знаний модели | `guards.py` + новый `citation_guard` нода | Высокий / Средняя |
| **A3** | **Порог релевантности retrieval** — если top score ниже порога или результат пуст → честный «не нашёл в учебнике», без генерации | Галлюцинации при слабом совпадении | `theory.py` / `retriever.py` (вернуть score), узел проверки | Высокий / Низкая |
| **A4** | **Hybrid retrieval (срез 2b)** — keyword ∪ embeddings на **pgvector** (решено §4), rerank top-10 → top-4 | Низкий recall на синонимах/перефразировании (сейчас только keyword) | `services/rag/` (новый `pgvector_store.py`; `vectorstore.py`/Chroma — dev-фолбэк) | **Высокий / Высокая** |
| **A5** | **Дедуп и ранжирование** результатов `retrieve_theory` (по `topic`+`chunk_idx`), обрезка по бюджету токенов | Дубли чанков раздувают контекст, размывают ответ | `tools.retrieve_theory` | Средний / Низкая |
| **A6** | **Лимиты графа** — `recursion_limit`, max tool-calls за сессию, суммаризация длинной истории при replay | Зацикливание tool-loop; рост стоимости и латентности на длинных диалогах | `graph.compile(...)`, `tutor_service._history_to_lc_messages` | Средний / Средняя |
| **A7** | **Профиль в PostgreSQL** (вместо JSON-файлов `tutor_profiles/`) | Файлы не переживают multi-worker/контейнер; нет RBAC | `repositories/app/` + миграция | Средний / Средняя |
| **A8** | **Query rewriting + multi-query retrieval** — адаптация вопроса ученика в 1–3 поисковых запроса с терминами учебника **до** `Retriever.search()`; merge результатов (§4) | Ложные «не нашёл в учебнике» при наличии контента; плохой `query` от ReAct; доминирование общих слов («металлы») над специфичными («сера») | `services/rag/query_rewrite.py`, `theory.py` / `tools.retrieve_theory`; опц. узел в `graph.py` | **Высокий / Средняя** |

**Порядок реализации (РЕШЕНО 2026-06-17, доп. 2026-06-18):** A4 + A5 (hybrid retrieval + дедуп/ранжирование) → **A8** (query rewriting, срез 16-1b) → A1 (solve-pipeline, этап A) → A6 → A7.
**Отложено:** A2 (citation guard) и A3 (порог retrieval) — ставка на то, что hybrid retrieval (A4)
сам поднимает точность теории; дешёвые guards вернём, если eval после hybrid покажет остаточные
галлюцинации/слабый retrieval. Обоснование смены порядка: корневая причина неточности (кейс «карбоновые
кислоты») — **слабый recall keyword-поиска**, а не отсутствие пост-проверок; чиним причину, а не симптом.

### 16.2 Новые возможности (что ещё агент может делать в проекте)

Агент сейчас изолирован от прикладных данных (ДЗ, история тестов, ошибки). Подключив их
через **новые tools**, советчик превращается из «чата по учебнику» в персонального тьютора.
Все student-tools соблюдают gating: во время активной `TestSession` — только теория.

#### Для ученика

| Tool (предлагается) | Что делает | Источник данных | Пример запроса |
|---------------------|-----------|-----------------|----------------|
| `get_my_homework()` | Список активных ДЗ ученика со статусом и сроком | `HomeworkService.list_assignments(user)` | «Что мне задано?» / «Какие дедлайны?» |
| `analyze_my_mistakes(limit=20)` | Разбор последних **неверных** шагов (по `type`/теме) → слабые темы | `TestSession.steps[]` (`is_correct=false`), агрегация по `type` | «Где я чаще ошибаюсь?» |
| `recommend_topics()` | Темы учебника под слабые места ученика | mistakes → маппинг `type`→`topic` → `prepared_lectures` | «Что мне повторить?» |
| `generate_practice(topic/type, n=5)` | Подобрать похожие задания для тренировки (без `correct_ans` в выдаче, только id+текст) | `search_tasks(task_type=…)` (уже есть) | «Дай 5 задач на органику» |
| `get_selfcheck(topic)` | Вопросы самопроверки из учебника | `prepared_lectures.qa_questions/qa_answers` (источник `lecture_qa` уже индексируется) | «Проверь меня по теме Алканы» |
| `explain_my_answer(test_id)` | Почему мой ответ неверный (**вне** активного теста) | `TestSession.steps` + `GradingService` + solve-pipeline (A1) | «Почему задание 12 неверно?» |

#### Для преподавателя

| Tool (предлагается) | Что делает | Источник данных |
|---------------------|-----------|-----------------|
| `summarize_student(student_id)` | Сводка: слабые темы, типичные ошибки, активность по диалогам/тестам | `TestSession` + `TutorSession` ученика (RBAC по teacher_id) |
| `suggest_homework(student_id)` | Черновик ДЗ под слабые темы ученика (преподаватель утверждает) | mistakes-анализ → `HomeworkCreate` items |
| `class_overview()` | Агрегат по всем ученикам: частые ошибки по `type` | `TestSession` всех учеников преподавателя |

> **Принцип:** агент только **готовит** черновик (например ДЗ) — финальное действие
> (создание `HomeworkAssignment`) подтверждает преподаватель через обычный UI/endpoint.
> Агент не делает write-операций без явного подтверждения пользователя (см. Boundaries).

### 16.3 UX и продуктовые улучшения

| # | Улучшение | Эффект |
|---|-----------|--------|
| U1 | **Streaming ответов (SSE)** — токены по мере генерации вместо ожидания всего ответа | Воспринимаемая скорость; критично при solve-pipeline (несколько LLM-вызовов) |
| U2 | **Markdown-рендер** в `MessageBubble` + sanitization (отложенный S2) | Формулы, списки, таблицы в разборах читаемы |
| U3 | **Suggested prompts по `page_context`** — на странице темы «Объясни кратко», на тесте «Подскажи теорию» | Снижает порог входа, направляет в on-topic |
| U4 | **Кнопка «спросить советчика» прямо из шага теста/разбора** — прокидывает `test_session_id`/`topic` в чат | Бесшовный переход обучение↔вопрос |

### 16.4 Наблюдаемость и оценка качества

| # | Что | Зачем |
|---|-----|-------|
| O1 | **Логирование tool-вызовов** (`get_task` id/type, кол-во hits retrieve_theory), латентности, токенов — `logging` на INFO | Отладка сценариев, контроль стоимости (риск §10) |
| O2 | **Eval-набор** `tests/tutor/eval/` — 10–20 вопросов с эталонными `topic`/`chunk_idx`, метрика **recall@5 ≥ 0.8** | Регресс качества RAG на каждый PR (есть в `RAG_chemistry`, нет в chim_web) |
| O3 | **Метрики runtime** — % off-topic, % пустого retrieval, среднее число tool-итераций | Понять, где агент «промахивается» |

### 16.5 Безопасность и стоимость (дополнения к §9)

- **Rate limiting** на `/api/tutor/.../messages` — при росте числа учеников (сейчас осознанно нет, §SPEC допущение 12).
- **Бюджет токенов** на сессию/ученика; мягкий лимит сообщений в окне.
- **Лимиты графа** (A6) как защита от runaway-стоимости при зацикливании.
- **Write-tools требуют подтверждения** — агент не создаёт/не меняет ДЗ, оценки, профиль чужого пользователя без явного действия владельца.

### 16.6 Acceptance criteria (дополнение к §11)

- [ ] AC-16.1 (A3): при retrieval ниже порога/пустом — ответ «не нашёл в учебнике», не выдуман.
- [ ] AC-16.2 (A2): ответ по теории всегда содержит ≥1 цитату из реально вызванного `retrieve_theory`.
- [ ] AC-16.3 (A1): «разбери задание N» вне теста → ключ в ответе == `correct_ans` (проверено кодом), есть цитата; во время теста — недоступно.
- [ ] AC-16.4 (T-tools): `get_my_homework`/`analyze_my_mistakes` возвращают данные только текущего ученика (RBAC), `correct_ans` не утекает во время активного теста.
- [ ] AC-16.5 (O2): eval-набор recall@5 ≥ 0.8 прогоняется в `pytest` без реального LLM (retrieval-часть).
- [ ] AC-16.6: все новые tools покрыты unit-тестами с mock LLM/DB.
- [ ] AC-16.7 (A8): на eval-кейсе «как с металлами реагирует сера?» (и аналогах) ожидаемый чанк `Cера` / `chunk_idx: 1` в top-5 **после** query rewriting; без rewriter кейс может оставаться в регрессионном наборе как контрольный промах keyword-only.

### 16.7 Рекомендуемая последовательность срезов

```
Срез 16-1: ТОЧНОСТЬ RAG (приоритет) — RAG-cleanup (убрать hint/detailed) + hybrid retrieval
           (keyword ∪ embeddings на pgvector, A4) + дедуп/ранжирование (A5) + eval-набор O2 + логи O1
Срез 16-1b: Адаптация запроса — query rewriting + multi-query (A8); eval-кейс «сера + металлы»
Срез 16-2: Solve-pipeline v1.5 — A1 + validation.py (порт RAG_chemistry), этап A → этап B
Срез 16-3: Персональный тьютор (ученик) — get_my_homework, analyze_my_mistakes, recommend_topics
Срез 16-4: Тренажёр — generate_practice + get_selfcheck + U3/U4 (suggested prompts) ✅ local (Task 44)
Срез 16-5: Преподаватель — summarize_student, suggest_homework (черновик)
Срез 16-6: UX — streaming (U1) + markdown (U2); профиль → PostgreSQL (A7)
Отложено:  A2 (citation guard) + A3 (порог retrieval) — вернуть после оценки hybrid на eval
```

> **Открытые вопросы по §16:**
> 1. Маппинг `type` → `topic` (для `recommend_topics`/`analyze_my_mistakes`) — есть ли явная таблица соответствия номера задания ЕГЭ/ОГЭ теме учебника, или выводить эвристикой через RAG по тексту задания?
> 2. `generate_practice` — отдавать задания только из банка трека ученика; нужен ли учёт уже решённых (не повторять)?
> 3. Streaming (U1) при solve-pipeline с несколькими LLM-узлами — стримить только финальный `solver`, или прогресс по узлам?

---

## 17. Solve-pipeline v1.5 — детальный дизайн (порт `RAG_chemistry` под chim_web)

> Конкретизирует §16.1 **A1**. Источник — `RAG_chemistry/SPEC.md` (расширение v1.5).
> Здесь зафиксированы **отличия порта** под chim_web: gating по `TestSession`, multi-user,
> треки ЕГЭ/ОГЭ, отсутствие `correct_ans` в ответе ученику во время теста.

### 17.1 Проблема (почему ReAct-v1 недостаточно для разбора заданий)

Текущая топология `input_guard → agent ⇄ tools → END` для сценария «разбери задание N»
держится только на system prompt. Наблюдаемые дефекты (см. §16.1):

1. LLM может **не вызвать** `get_task(N)` — разбор «по памяти».
2. Финальный ключ **не сверяется** с `correct_ans` из БД.
3. Пошаговый разбор и итоговый ключ могут **расходиться**.
4. RAG **формальный** — цитата не обязательна, ответ из знаний модели.
5. **Нет пост-валидации** перед отправкой ученику.

**Принцип решения:** доступ к данным (`get_task`, `retrieve_theory`) и проверку ключа
выполняет **код графа**, а не LLM. LLM отвечает только за объяснение.

### 17.2 Топология графа (расширение)

```
START → input_guard → intent_router
                          │
        ┌─────────────────┼────────────────────┐
        ▼                 ▼                     ▼
  general_agent      solve_pipeline        off_topic → END
  (теория/профиль,   (только ВНЕ              (как сейчас)
   как сейчас)        активного теста)
   agent ⇄ tools          │
        │                 ▼
        ▼          prepare_context  (КОД: extract_task_id → get_task → retrieve_theory)
       END                ▼
                     [planner]  (LLM → SolvePlan; только для сложных типов 7,8,26–28)
                          ▼
                     solver  (LLM: разбор по готовому контексту; ключ из correct_ans)
                          ▼
                     critic  (КОД: ключ/цитата/формат + LLM: химия)
                          │
              ┌───────────┴───────────┐
              ▼ approved              ▼ rejected (retry < 2)
             END                   → solver (fix_instructions)
                                  иначе → answer_finalize → END
```

**Узлы:**

| Узел | Тип | Ответственность |
|------|-----|------------------|
| `intent_router` | код | regex `задани[ея]/задач[ау]` + номер → `solve_pipeline`; **+ проверка активной `TestSession`**: при активном тесте → `general_agent` (только теория) |
| `prepare_context` | код | `extract_task_id`; `get_task` (через `tutor/tasks.py`); проверка `requires_image`; `retrieve_theory`; заполняет state |
| `planner` | LLM | `SolvePlan` (уточняющие rag-запросы, sub-steps, формат ответа); только для сложных типов |
| `solver` | LLM | разбор по `task_context` + `theory_hits`; ключ берётся из `correct_ans`, не «выводится» |
| `critic` | код+LLM | код: ключ/цитата/формат (`validation.py`); LLM: согласованность химии |
| `answer_finalize` | код | при исчерпании ретраев — гибрид: разбор + явно выделенный эталонный `correct_ans` + дисклеймер |

### 17.3 Контракты данных (Pydantic / state)

DTO — в `app/schemas/tutor.py` (или `app/services/tutor/solve/state.py`):

```python
class SolvePlan(BaseModel):
    intent: Literal["solve_task", "theory", "search_tasks", "profile", "other"]
    task_id: int | None = None
    rag_queries: list[str] = Field(default_factory=list)   # 1–3 запроса к учебнику
    sub_steps: list[str] = Field(default_factory=list)
    # "digit_string" — цифры в порядке АБВГ (типы 1–24); "number" — десятичное (26–28)
    answer_format: Literal["digit_string", "number"]

class Critique(BaseModel):
    approved: bool
    issues: list[str] = Field(default_factory=list)
    fix_instructions: str = ""

class SolveState(MessagesState):          # расширение MessagesState
    plan: SolvePlan | None
    task_context: dict | None             # question, type, requires_image (БЕЗ correct_ans наружу)
    correct_ans: str | None               # серверное, в ответ ученику не утекает дословно
    theory_hits: list[dict]
    draft_answer: str | None
    critique: Critique | None
    retry_count: int
```

> **Отличие от RAG_chemistry:** `correct_ans` хранится в state **только серверно**;
> в `solver`/`critic` используется для сверки, но в финальном ответе ученику показывается
> как часть разбора (а не как «слитый ключ» во время теста — там solve-ветка вообще выключена).

### 17.4 Проверки критика (детерминированная часть — `validation.py`)

Новый модуль `app/services/tutor/validation.py` (переиспользуется в графе и тестах):

| Проверка | Логика | Issue при провале |
|----------|--------|-------------------|
| Ключ `digit_string` | нормализация (без пробелов/разделителей), сравнение **посимвольно без переупорядочивания**, порядок АБВГ | `"ключ X ≠ correct_ans Y"` |
| Ключ `number` | числовое сравнение с допуском: `,`↔`.`, отбрасывание единиц («3,35 моль» → 3.35) | `"число X ≠ correct_ans Y"` |
| Наличие цитаты | хотя бы один `topic`/`chunk_title` из `theory_hits` упомянут в ответе | `"нет ссылки на учебник"` |
| Согласованность соответствий (тип 7/8) | поэлементная разметка (А→…, Б→…) совпадает с цифрами итогового ключа по позициям | `"разбор противоречит ключу"` |
| Условие из БД | ключевые фрагменты `question` из `get_task` присутствуют в разборе | `"условие не из БД"` |

LLM-критик добавляет содержательную химическую проверку и возвращает `Critique`.

> **Переиспользование:** часть нормализации ответа уже есть в `GradingService.normalize_answer`
> (тесты Stepik). `validation.py` для агента может опираться на ту же нормализацию для
> `digit_string`, добавив числовой режим и проверку цитаты/согласованности.

### 17.5 Gating (отличие chim_web от RAG_chemistry CLI)

- **Вне активного теста:** полный solve-pipeline; ключ сверяется с `correct_ans` кодом; разбор показывается ученику.
- **Во время активной `TestSession` ученика:** `intent_router` направляет в `general_agent`; `get_task` уже блокируется в `tools.py` (реализовано); solve-ветка недоступна.
- Проверка активной сессии — через `TutorRunContext.active_test_session_id` (уже прокидывается в `tutor_service._build_run_context`).

### 17.6 Сложные vs простые типы (когда нужен planner)

| Класс | Типы | Путь |
|-------|------|------|
| Простые | 1–6, 9–24 (один вопрос / однозначный `digit_string`) | `prepare_context → solver → critic` (без planner) |
| Сложные | соответствия **7, 8**; расчётные **26, 27, 28** | `prepare_context → planner → solver → critic` |
| Пограничный | **25** (бывает и `digit_string`, и число) | уточнить на реализации (open question §16) |

### 17.7 Этапность реализации (внутри среза 16-2)

1. **Этап A (минимум):** `intent_router` + `prepare_context` + `validation.py` + код-критик (ключ/цитата/формат) **без planner**. Уже закрывает дефекты 1, 2, 4, 5.
2. **Этап B:** `planner` + LLM-критик (химическая согласованность) для сложных типов. Закрывает дефект 3.

Каждый этап — независимо тестируемый инкремент (см. `02-incremental-implementation`).

### 17.8 Acceptance criteria (solve-pipeline)

- [ ] AC-17.1: «разбери задание N» вне теста → в логах виден вызов `get_task(N)`; финальный ключ == `correct_ans` после нормализации.
- [ ] AC-17.2: в разборе есть цитата (`topic`/`chunk_title`) из реально вызванного `retrieve_theory`.
- [ ] AC-17.3: критик отбраковывает черновик с ключом ≠ `correct_ans` и инициирует retry; цикл ≤2 ретрая.
- [ ] AC-17.4: во время активной `TestSession` solve-ветка не запускается (только теория) — регрессионный тест.
- [ ] AC-17.5: `validation.py` unit-тесты: `digit_string` (вкл. соответствия), `number` (с «хвостом» единиц), отсутствие цитаты.
- [ ] AC-17.6: общий чат по теории/профилю работает без регрессий (прежние tutor-тесты зелёные).

---

*Changelog:*  
- 0.8.2 — §4 **адаптация запроса (query rewriting)**: зафиксированы проблема (кейс «сера + металлы»), multi-query retrieval, мягкий сигнал `page_context.topic`, фичефлаг; §16.1 **A8**; AC-16.7; срез **16-1b** / Task **41.4** в плане.  
- 0.8.1 — §3 tools приведены к реализации (`retrieve_theory`, `get_task`, `search_tasks`, `save_user_info`); **`get_test_explanation` удалён** (RAG только учебник, §2); §12.3 pgvector vs Chroma закрыт.  
- 0.8 — **Точность агента (решения владельца 2026-06-17, «лучшее из `RAG_chemistry`»):** (1) §4 — целевой retrieval зафиксирован как **hybrid (keyword ∪ embeddings) на pgvector**, приоритет №1; Chroma → dev-фолбэк; `page_context.topic` решено **не** использовать в поиске. (2) §2 — `tests.hint`/`detailed_explanation` **исключены** из RAG-индекса; разбор агент строит сам от теории (как в оригинале). (3) §16 — переприоритизация: точность RAG (A4/A5) → solve-pipeline (A1); guards A2/A3 **отложены**. Реализация — план Phase 10: **Task 41 переориентирован** на точность RAG (cleanup + hybrid + eval), guards вынесены в **Task 46 (отложено)**.  
- 0.7 — §17 детальный дизайн solve-pipeline v1.5 под chim_web: топология (intent_router/prepare_context/planner/solver/critic/answer_finalize), контракты (`SolvePlan`/`Critique`/`SolveState`), правила `validation.py`, gating по `TestSession`, сложные vs простые типы, этапность A/B, AC-17.x. Уточняет §16.1 A1.  
- 0.6 — §16 «Надёжность и расширение агента»: приоритизированный roadmap надёжности (A1–A7: solve-pipeline, citation guard, порог retrieval, hybrid RAG, лимиты графа, профиль в PG), новые возможности через tools, привязанные к данным проекта (ДЗ, история тестов, слабые темы, тренажёр, сводки для преподавателя), UX (streaming, markdown, suggested prompts), наблюдаемость/eval, безопасность/стоимость, AC-16.x и порядок срезов.  
- 0.5 — Task 38 выполнен: закрыты I1–I7, S1, S3, S4 и B1–B4; граф stateless с replay истории из PostgreSQL (B1), off-topic guard на каждое сообщение (B3), health под auth (B4), 2-фазный commit + timeout + rollback в `send_message` (I2–I5, I7), frontend overlay loading/опубликован сброс контекста (I1, I6, S1). Отложено S2 (markdown). §7 и §10 обновлены.  
- 0.4 — §15 round 2 (2026-06-17): обзор всего tutor-слоя — B1 (память/checkpointer), B2 (порядок transcript), B3 (off-topic guard), B4 (public health); уточнение §7 про расхождение реализации.  
- 0.3 — §15 code review findings (2026-06-17): `send_message` NFR, `page_context` lifecycle, UX loading, регрессионные тесты.  
- 0.2 — §14 интеграция готового `RAG_chemistry`; UI переведён на overlay-панель; решён open question про поведение на экране теста (gating).  
- 0.1 — первичный черновик по ревью с владельцем продукта.
