# Spec: AI-советчик (Agent + RAG)

**Версия:** 0.1  
**Дата:** 2026-06-09  
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
| Тесты ЕГЭ/ОГЭ | `tests` | `hint`, `detailed_explanation` + `filename`, `type`, track | `test` |

**Не индексировать:** `correct_ans`, `tts_audio`, BLOB.

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
source: test
track: ege
variant: 003.txt
type: 15
field: detailed_explanation
---
{markdown}
```

### Метаданные (для фильтрации retrieval)

```python
class RagDocumentMeta(TypedDict, total=False):
    source: Literal["lecture", "lecture_qa", "test"]
    topic: str
    chunk_idx: int
    chunk_title: str
    track: Literal["ege", "oge"]
    variant: str
    test_type: int
    field: Literal["hint", "detailed_explanation", "question", "answer"]
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
│       ├── tools.py        # @tool search_textbook, get_lecture_chunk, ...
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
| `search_textbook` | RAG по всем источникам; опционально `topic`, `track` | student, teacher |
| `get_lecture_chunk` | Полный чанк по `topic` + `chunk_idx` | student, teacher |
| `get_test_explanation` | `hint` или `detailed_explanation` по variant+type | student, teacher |
| `get_student_context` | Трек, активное ДЗ (без ответов тестов) | student only |

**Запрещённые данные в tools:** `correct_ans`, сырые ответы других учеников.

### LangGraph (паттерн)

По образцу учебного `airline_react_agent.py`:

```
START → input_guard → agent ⇄ ToolNode → tool_output_guard → agent → END
```

- `parallel_tool_calls=False` — один tool за шаг.
- System prompt: «сначала `search_textbook` для теории; не выдумывай; цитируй sources».

---

## 4. Retrieval strategy

### Рекомендация (зафиксировано в spec)

| Срез | Реализация | Критерий готовности |
|------|------------|---------------------|
| **2a** | Keyword/BM25 (`keyword_score` по title+body, RU stop-words) | 10 эталонных вопросов → top-3 содержит ожидаемый чанк |
| **2b** | Hybrid: keyword ∪ vector, rerank top-10 → top-4 | Улучшение recall на перефразированных вопросах |

**Хранилище embeddings (2b):** `pgvector` в PostgreSQL (рядом с app DB). Альтернатива — Chroma file-based; решение в ADR при implement.

**CLI индексации:**

```bash
cd backend
python -m app.cli.index_rag --rebuild
```

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
| Глобальный чат (панель / страница `/tutor`) | student | P2 |
| Список сессий ученика + transcript | teacher | P2 |

**UX:**

- Показ `sources` как кликабельные ссылки: «Алканы → Свойства алканов».
- Индикатор «ищу в учебнике…» на время tool-вызовов.
- Markdown в ответах с sanitization.

---

## 7. Persistence (PostgreSQL)

```sql
-- концептуально
tutor_sessions (id, user_id, role_context, page_context jsonb, created_at, updated_at)
tutor_messages (id, session_id, role, content, sources jsonb, created_at)
rag_embeddings (id, doc_id, source, metadata jsonb, embedding vector)  -- срез 2b
```

История **не** в LangGraph MemorySaver как единственное хранилище — checkpointer опционален; source of truth — PostgreSQL.

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
| E2E (опционально) | 3 эталонных вопроса с реальным LLM в CI nightly |

**Не вызывать** реальный LLM в `pytest` по умолчанию.

---

## 11. Acceptance criteria

- [ ] AC-6.1 … AC-6.6 из `SPEC.md` US-6.
- [ ] Индекс пересобирается CLI без ручных шагов.
- [ ] Retriever: 8/10 эталонных вопросов → ожидаемый чанк в top-3 (срез 2a).
- [ ] Agent trace: минимум один вызов `search_textbook` на теоретический вопрос.
- [ ] Teacher не может читать сессии чужих учеников (403).

---

## 12. Open questions (до implement)

1. **Поведение на экране теста** — теория only / `get_hint` tool / чат disabled. Решить на пилоте.
2. **LLM провайдер** — OpenAI vs OpenRouter vs local.
3. **pgvector vs Chroma** — ADR при старте среза 2b.
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

*Changelog:*  
- 0.1 — первичный черновик по ревью с владельцем продукта.
