# SPEC — Chemistry (chim_web)

**Версия:** 0.5  
**Дата:** 2026-06-09  
**Статус:** частично согласован (добавлен §1.6 AI-советчик)  
**Стек:** FastAPI + Next.js (monorepo `chim_web`, см. `AGENTS.md`)

---

## ДОПУЩЕНИЯ

> Поправь сейчас — иначе план и реализация пойдут с этими предположениями.

| # | Область | Допущение |
|---|---------|-----------|
| 1 | **Контентные БД** | `test_ege.db`, `test_oge.db`, `prepared_lectures.db` остаются **read-only** источниками на MVP. Backend читает их через SQLite (attach / отдельные connection pool). Миграция контента в PostgreSQL — **не в v1**, unless иначе решим на ревью. |
| 2 | **Прикладная БД** | PostgreSQL 16+ для пользователей, связей «преподаватель ↔ ученики», домашних заданий, попыток, уведомлений. SQLAlchemy 2.x + Alembic. |
| 3 | **Auth** | Email + пароль. Роли: `teacher`, `student`. JWT в **httpOnly cookies** (`credentials: 'include'`), не в `localStorage`. Один преподаватель на инстанс MVP; учеников создаёт/привязывает только преподаватель. |
| 4 | **Онбординг** | Преподаватель вручную создаёт учётки учеников (логин/временный пароль) или выдаёт одноразовый invite-код. Self-registration учеников — **вне v1**. |
| 5 | **Треки** | У ученика один активный трек: **ЕГЭ** или **ОГЭ** (задаёт преподаватель при создании/в профиле). Контент второго трека скрыт. |
| 6 | **Домашнее задание** | Преподаватель назначает: (а) тему/чанки учебника — ученик отмечает «Прочитано»; (б) **целый вариант** теста; (в) **подмножество заданий** из варианта (номера `type`). Срок сдачи опционален. |
| 6a | **Подсказки в тестах** | `hint` показывается **только по запросу** ученика (кнопка «Подсказка»), не автоматически. |
| 6b | **Порядок тем учебника** | Как в `prepared_lectures.db`: порядок первого появления темы (`ORDER BY MIN(rowid)`), не алфавит. |
| 7 | **Уведомления** | In-app (колокольчик + список) на MVP. Email / Telegram / push — **вне v1**. |
| 8 | **Деплой** | Dev: локально (venv + `npm run dev`). Prod: Docker Compose на VPS (nginx → Next + FastAPI + PostgreSQL). CI — GitHub Actions (lint + pytest + build) — **после** первого рабочего среза. |
| 9 | **Язык UI** | Русский. |
| 10 | **AI** | **Вне scope v1:** чат-советчик (Agent + RAG) и AI-проверка письменных заданий. В v1 поля `hint` / `detailed_explanation` — статический контент из БД. AI-советчик — **v2+** (см. §1.6, детали: `docs/specs/tutor-rag.md`). Архитектуру проверки ответов закладываем расширяемой (см. §1.4). |
| 11 | **UX тестов** | Организация прохождения — **в стиле Stepik**: пошаговый сценарий, одно задание на экран, мгновенная проверка, навигация по шагам, прогресс. |
| 12 | **AI-советчик** | Доступен **ученику и преподавателю** (разные system prompt / права tools). UI — **глобальный чат** в кабинете. История диалогов — **PostgreSQL**; преподаватель может просматривать диалоги своих учеников. Провайдер LLM — **абстракция** (конкретный vendor — до реализации). Rate limit на v2+ — **нет** (мало пользователей). |

---

## 1. Objective

### Что строим

Веб-приложение для **репетитора по химии** и его **учеников**:

| Роль | MVP-возможности |
|------|-----------------|
| **Ученик** | Учебник (лекции по темам), тесты ЕГЭ/ОГЭ, выполнение домашних заданий |
| **Преподаватель** | Список учеников, назначение ДЗ, просмотр статуса/результатов, уведомления о сдаче |

### Зачем

Централизовать учебные материалы (уже подготовленные в SQLite) и цикл «назначил ДЗ → ученик сделал → преподаватель увидел» без разрозненных файлов и мессенджеров.

### Для кого

- 1 преподаватель (владелец контента)
- N учеников (типично 5–30 на MVP)

### Источники контента (изучено)

#### `prepared_lectures.db` — учебник

| Таблица | Строк | Назначение |
|---------|------:|------------|
| `prepared_lectures` | 185 | Чанки лекций по темам |

**Схема:** PK `(topic, chunk_idx)`

| Поле | Тип | Описание |
|------|-----|----------|
| `topic` | TEXT | Тема (31 тема: «Алканы», «Соли», «ОВР», …) |
| `chunk_idx` | INT | Порядковый номер чанка в теме (0…n) |
| `chunk_title` | TEXT | Заголовок чанка |
| `orig_text` | TEXT | Исходный текст учебника |
| `lecture` | TEXT | Переработанная лекция (markdown-подобный текст) |
| `tts_text` | TEXT | Текст для озвучки |
| `tts_audio` | BLOB | Аудио OGG (~0.5–2 MB на чанк) |
| `tts_audio_format` | TEXT | `ogg` |
| `duration_ms` | INT | Длительность аудио |
| `qa_questions` | TEXT | JSON-массив вопросов для самопроверки |
| `qa_answers` | TEXT | JSON-массив ответов |

#### `test_ege.db` — тесты ЕГЭ

| Таблица | Строк | Назначение |
|---------|------:|------------|
| `tests` | 840 | Задания |
| `images` | 21 | PNG-рисунки (`рисунок0000.png` …) |
| `tests_bug` | 3 | Задания с пометкой `has_issue=1` (исключить из выдачи на MVP) |

**Содержимое v1:** в БД сейчас **только тестовые задания** с кратким ответом (`correct_ans` — цифры/короткие строки). Письменных заданий (развёрнутый ответ, II часть) **в контентных БД пока нет** — появятся позже.

**Структура вариантов:** 30 файлов-вариантов (`001.txt` … `030.txt`), в каждом **28 типов заданий** (`type` 1–28) — тестовая часть варианта ЕГЭ.

**Схема `tests`:**

| Поле | Описание |
|------|----------|
| `filename` | Идентификатор варианта (`NNN.txt`) |
| `type` | Номер задания в варианте (1–28) |
| `question` | Текст; рисунки — плейсхолдеры `[рисунок0001]` |
| `options` | Доп. данные (часто пусто; для заданий на соответствие — номера позиций) |
| `correct_ans` | Строка с цифрами ответа (`23`, `422`, …) |
| `hint` | Подсказка (markdown) |
| `detailed_explanation` | Разбор (markdown) |
| `has_issue` | Флаг проблемного задания |

#### `test_oge.db` — тесты ОГЭ

Та же схема, что у ЕГЭ.

| Таблица | Строк |
|---------|------:|
| `tests` | 570 |
| `images` | 26 (`OGE0001.png` …) |
| `tests_bug` | 0 |

**Содержимое v1:** как и в ЕГЭ — только **тестовые задания** с автопроверяемым кратким ответом.

**Структура:** 19 типов заданий (`type` 1–19), по **30 вариантов** на тип (`filename` `001.txt` … `019.txt` — привязка к типу, не к полному варианту как у ЕГЭ).

### 1.3 UX тестов (референс: Stepik)

MVP повторяет **паттерн пошагового урока** Stepik, а не «все вопросы на одной странице»:

```
Выбор варианта / ДЗ
       │
       ▼
┌──────────────────────────────────────┐
│  Шаг 3 из 28          [████░░░░]     │  ← прогресс
├──────────────────────────────────────┤
│  Текст задания + рисунки             │
│  [ поле ответа ]                     │
│  [ Подсказка ]  [ Проверить ]        │  ← hint по запросу
├──────────────────────────────────────┤
│  ✓ Верно / ✗ Неверно               │  ← сразу после «Проверить»
│  [ Разбор ] (detailed_explanation)   │  ← после проверки
│  [ ← Назад ]  [ Далее → ]           │
└──────────────────────────────────────┘
       │
       ▼
Итог: балл, список шагов, что верно/неверно
```

| Элемент Stepik | Реализация в v1 |
|----------------|-----------------|
| Один шаг = одно задание | Одна `type` / один `test.id` на экран |
| Кнопка «Проверить» | `POST` ответа на текущий шаг → `{ correct, feedback? }` |
| Мгновенная обратная связь | Зелёный/красный статус сразу после проверки |
| Подсказка по запросу | Кнопка «Подсказка» → `hint` из БД |
| Навигация по шагам | «Назад» / «Далее»; переход к любому уже открытому шагу |
| Прогресс | «Шаг N из M» + progress bar |
| Итог урока | Экран сводки: score / max, разбор по шагам |
| Повторная попытка | На шаге можно изменить ответ и нажать «Проверить» снова (история попыток в app DB) |

**Сессия прохождения:** `TestSession` в app DB — привязка к ученику, варианту, списку `test_id`, статусу каждого шага (`unseen` → `answered` → `checked`).

**Свободная практика vs ДЗ:** один и тот же step-UI; ДЗ ограничивает набор шагов и триггерит уведомление преподавателю при завершении сессии.

### 1.4 Типы контента: тестовые vs письменные

| Тип | В БД сейчас | v1 | v2+ |
|-----|-------------|----|-----|
| **Тестовые** (краткий ответ, `correct_ans`) | ✅ ЕГЭ 1–28, ОГЭ 1–19 | Выдаём, `grading_mode=exact` | Без изменений |
| **Письменные** (развёрнутый ответ, уравнения, расчёты) | ❌ Нет в БД | — | Добавить контент + **AI-проверка** |

**Решение:** письменные задания при добавлении в БД **не показывать ученикам**, пока не готова AI-проверка (v2). Фильтр: `grading_mode != exact` → скрыто из API/UI.

### 1.5 Roadmap: AI-проверка письменных (post-MVP)

| Фаза | Что | Проверка |
|------|-----|----------|
| **v1** | Весь текущий контент — тестовые задания | Exact match после нормализации |
| **v2** | Импорт письменных заданий в content DB | `grading_mode: ai_assisted` — LLM + rubric; преподаватель подтверждает/переоценивает |
| **v2+** | AI-советчик (Agent + RAG) | LangGraph-агент + retrieval по учебнику и тестам; см. §1.6 |

**Заложить в v1 (модель, без LLM):**

```python
grading_mode: Literal["exact", "ai_assisted", "manual"] = "exact"

# Content repo: WHERE grading_mode = 'exact'  — единственное, что видит ученик в v1
# StudentAnswer: raw_text, normalized_text, is_correct, ai_feedback (nullable)
```

### 1.6 Roadmap: AI-советчик (Agent + RAG) — v2+

> **Детальная спека:** [`docs/specs/tutor-rag.md`](docs/specs/tutor-rag.md)

#### Что строим

Чат-помощник по химии для подготовки к ЕГЭ/ОГЭ. Два компонента:

| Компонент | Назначение |
|-----------|------------|
| **RAG** | Поиск релевантных фрагментов в контентных БД перед ответом |
| **Agent** | LangGraph ReAct: решает, какие tools вызвать, собирает ответ с цитатами |

#### Источники для RAG (v2+ старт)

| Источник | Поля | `source` в метаданных |
|----------|------|------------------------|
| `prepared_lectures.db` | `topic`, `chunk_idx`, `chunk_title`, `lecture` | `lecture` |
| `prepared_lectures.db` | `qa_questions`, `qa_answers` (JSON) | `lecture_qa` |
| `test_ege.db` / `test_oge.db` | `hint`, `detailed_explanation` (+ `filename`, `type`) | `test` |

Контентные БД остаются **read-only**; индекс строится offline, embeddings хранятся отдельно от SQLite.

#### Retrieval (рекомендация spec)

| Срез | Подход | Обоснование |
|------|--------|-------------|
| **2a** | Keyword/BM25 по чанкам (~200+ документов) | Быстрый старт без vector DB; паттерн как `lookup_policy` в учебном авиа-агенте |
| **2b** | Hybrid: keyword + embeddings (pgvector в PostgreSQL) | Лучше на синонимах и перефразировании; интерфейс `Retriever.search()` не меняется |

#### UI и роли

- **Ученик:** глобальный чат в кабинете; контекст страницы (тема лекции, активный тест) передаётся в API опционально.
- **Преподаватель:** тот же чат + просмотр истории диалогов учеников (read-only).
- Поведение агента **во время теста** — **TBD** до пилота (см. §12, вопрос 6).

#### Границы (v2+)

- Агент **не выдумывает** факты: ответ только на основе результатов tools.
- `correct_ans` **никогда** не передаётся в tools/prompt агента.
- API ключи LLM — только backend `.env`, не frontend.
- Off-topic запросы отклоняются (guardrail).

#### Success criteria (v2+, дополнение к MVP)

- [ ] Ученик задаёт вопрос по теории → агент вызывает RAG → ответ с ссылками на тему/чанк.
- [ ] При пустом retrieval агент сообщает, что в учебнике не нашёл (не галлюцинирует).
- [ ] История чата сохраняется в PostgreSQL и восстанавливается по `session_id`.
- [ ] Преподаватель видит список сессий ученика и transcript.
- [ ] `pytest` покрывает retriever, tools и endpoint без реальных вызовов LLM (mock).

### Success criteria (тестируемые)

- [ ] Ученик с ролью `student` и треком ЕГЭ видит список тем учебника и может открыть чанк (текст + аудио).
- [ ] Ученик с треком ОГЭ видит тесты ОГЭ, не видит ЕГЭ (и наоборот).
- [ ] Тест проходится **пошагово** (Stepik-style): одно задание на экран, «Проверить» → мгновенный результат, прогресс, итоговая сводка.
- [ ] Ученик проходит назначенный вариант или выбранные номера заданий; ответы проверяются по `correct_ans`; результат сохраняется.
- [ ] Подсказка (`hint`) доступна только по явному запросу ученика.
- [ ] ДЗ-лекция закрывается кнопкой «Прочитано».
- [ ] Рисунки из `images` подставляются в текст вопроса вместо `[рисунокNNNN]` / ссылок на OGE-изображения.
- [ ] Преподаватель создаёт ДЗ ученику; ученик видит его в списке «Мои задания».
- [ ] После сдачи ДЗ преподаватель получает **in-app уведомление** и видит результат в карточке ученика.
- [ ] Задания из `tests_bug` / с `has_issue=1` **не попадают** в выдачу ученику.
- [ ] `pytest` (backend) и `vitest` (frontend) зелёные для покрытых сценариев.

### Вне scope v1

- AI-агент / чат-советчик (Agent + RAG) — **v2+**, см. §1.6
- **Письменные задания и AI-проверка** (контента пока нет; roadmap v2, см. §1.4–1.5)
- Self-registration, OAuth, несколько преподавателей / школ
- Редактирование контента в UI
- Email/Telegram-уведомления
- Рейтинги, геймификация, расписание занятий
- Мобильное нативное приложение
- Отчёты/analytics beyond базового статуса ДЗ

---

## 2. Commands

### Dev

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run dev                     # http://localhost:3000
```

**Env (минимум):**

```env
# backend/.env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/chemistry
CONTENT_EGE_DB_PATH=../test_ege.db
CONTENT_OGE_DB_PATH=../test_oge.db
CONTENT_LECTURES_DB_PATH=../prepared_lectures.db
JWT_SECRET=...
CORS_ORIGINS=http://localhost:3000

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Test / quality

```bash
cd backend && pytest
cd backend && pytest --cov=app
cd backend && ruff check .
cd backend && mypy app/

cd frontend && npm run test
cd frontend && npm run lint
cd frontend && npm run build
```

### Migrations

```bash
cd backend && alembic upgrade head
```

### Prod (целевое, после реализации)

```bash
docker compose up -d --build
```

---

## 3. Project Structure

```
chim_web/
├── SPEC.md
├── test_ege.db                 # read-only контент
├── test_oge.db
├── prepared_lectures.db
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routers/
│   │   │   ├── auth.py
│   │   │   ├── textbook.py      # темы, чанки, аудио
│   │   │   ├── tests.py         # варианты, вопросы, проверка
│   │   │   ├── homework.py      # ДЗ CRUD, сдача
│   │   │   ├── students.py      # список учеников (teacher)
│   │   │   ├── notifications.py
│   │   │   └── tutor.py         # v2+: чат Agent + RAG
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── rag/             # v2+: indexer, retriever, store
│   │   │   └── tutor/           # v2+: LangGraph agent, tools, guards
│   │   ├── repositories/
│   │   │   ├── content/         # read-only SQLite
│   │   │   └── app/             # PostgreSQL
│   │   ├── models/              # ORM только app DB
│   │   ├── core/                # config, security, deps
│   │   └── db/
│   ├── tests/
│   └── alembic/
└── frontend/
    ├── app/
    │   ├── (auth)/login/
    │   ├── (student)/
    │   │   ├── textbook/[topic]/
    │   │   ├── tests/
    │   │   ├── homework/
    │   │   └── tutor/           # v2+: глобальный чат (student)
    │   └── (teacher)/
    │       ├── students/
    │       ├── homework/
    │       ├── notifications/
    │       └── tutor/           # v2+: чат + просмотр сессий учеников
    ├── components/
    │   └── tutor/               # v2+: TutorChat, SourceCitation
    └── lib/api/
```

### Ключевые сущности (app DB)

```
User (teacher | student)
  └── StudentProfile (track: ege | oge, teacher_id)

HomeworkAssignment
  ├── student_id, teacher_id
  ├── title, description
  ├── due_at (nullable)
  ├── items[]: { kind: lecture | test_variant | test_partial, ref... }
  │             test_variant: { variant: "003.txt" }           # все type варианта
  │             test_partial:  { variant: "003.txt", types: [10,11,15] }
  │             lecture:       { topic, chunk_idxs[]? }        # сдача = «Прочитано»
  └── status: assigned | in_progress | submitted | reviewed

TestSession                          # пошаговое прохождение (Stepik-style)
  ├── student_id, track, variant_ref, test_ids[]
  ├── homework_assignment_id (nullable)
  └── steps[]: { test_id, answer, is_correct, hint_used, checked_at }

HomeworkSubmission
  ├── assignment_id, submitted_at, test_session_id?
  └── score, max_score

Notification
  ├── user_id, type, payload, read_at
  └── created_at

TutorSession (v2+)
  ├── user_id, role_context (student | teacher)
  ├── page_context (nullable): { topic?, test_session_id?, homework_id? }
  └── created_at, updated_at

TutorMessage (v2+)
  ├── session_id, role (user | assistant | tool)
  ├── content, sources[] (nullable): { source, topic?, chunk_idx?, variant?, type? }
  └── created_at
```

---

## 4. Code Style

Следуем `AGENTS.md`:

- **Backend:** type hints, Pydantic v2, `Depends`, Router → Service → Repository, `HTTPException` на границах.
- **Frontend:** App Router, Server Components по умолчанию, `'use client'` только для интерактива, API через `lib/api/`.
- **Контент:** не смешивать SQLite content models с PostgreSQL ORM; отдельный слой `repositories/content/`.

**Пример контракта (фрагмент):**

```python
# GET /api/textbook/topics
# Response: list[{ topic: str, chunk_count: int }]

# GET /api/textbook/topics/{topic}/chunks/{idx}
# Response: { topic, chunk_idx, chunk_title, lecture, has_audio: bool }
# GET /api/textbook/topics/{topic}/chunks/{idx}/audio → audio/ogg stream

# POST /api/homework/{id}/submit
# Body: { answers: [{ test_id, answer: str }] }
# Response: { score, max_score, details[] }
```

---

## 5. Testing Strategy

### Пирамида

| Уровень | Backend | Frontend |
|---------|---------|----------|
| Unit | services: проверка ответов, парсинг плейсхолдеров изображений | utils, formatters |
| Integration | TestClient + test PostgreSQL; content repos на копии SQLite fixture | MSW + vitest |
| E2E (позже) | — | Playwright: login → открыть лекцию → сдать ДЗ |

### Обязательные сценарии (первый срез)

1. Auth: login teacher/student, 403 при доступе к чужому ДЗ.
2. Textbook: список тем, чанк без утечки `tts_audio` в JSON (только URL/stream).
3. Tests: подстановка image URL; фильтр `has_issue=1`; проверка `correct_ans`.
4. Homework: assign → submit → notification для teacher.
5. Track isolation: student `oge` не получает EGE tests.

### Coverage

- Критичная бизнес-логика (проверка ответов, RBAC, notifications) — ≥80% в затронутых модулях.

---

## 6. Boundaries

### Always

- Тесты перед коммитом для затронутого кода.
- Валидация входа (Pydantic / Zod на клиенте только для UX).
- Секреты в `.env`, не в git.
- RBAC на каждом endpoint: teacher vs student.
- Content DB — только SELECT.

### Ask first

- Смена схемы PostgreSQL (миграции согласовать).
- Перенос контента из SQLite в PostgreSQL.
- Новые крупные зависимости.
- Изменение формата `correct_ans` / логики проверки.
- Подключение LLM-провайдера и зависимостей LangGraph / embedding-моделей (v2+).

### Never (v2+ AI)

- Отдавать `correct_ans` агенту или в prompt чата.
- Вызывать LLM API с frontend; ключи только в backend `.env`.
- Индексировать или изменять контентные SQLite БД из runtime агента.

### Never

- Секреты в коде.
- Сырой SQL со строками пользователя.
- JWT в `localStorage`.
- Удаление падающих тестов без явного одобрения.
- Выдача `tests_bug` / `has_issue=1` ученикам.

---

## 7. User Stories & Acceptance (MVP)

### US-1: Учебник (ученик)

**Как** ученик, **хочу** читать лекции по темам и слушать аудио, **чтобы** повторять материал.

| AC | Критерий |
|----|----------|
| AC-1.1 | Список тем = distinct `topic` из `prepared_lectures`, порядок как в БД (`ORDER BY MIN(rowid)`): Алканы → … → Хром, марганец и алюминий (31 тема) |
| AC-1.2 | Внутри темы — чанки по `chunk_idx` с `chunk_title` |
| AC-1.3 | Текст лекции рендерится из поля `lecture` (markdown) |
| AC-1.4 | Аудио стримится отдельным endpoint; формат `ogg` |
| AC-1.5 | Блок самопроверки: `qa_questions` / `qa_answers` (раскрывающиеся ответы) — опционально на MVP, если успеем |

### US-2: Тесты (ученик, Stepik-style)

**Как** ученик, **хочу** решать тесты пошагово с мгновенной проверкой, **чтобы** готовиться к экзамену в привычном формате (как на Stepik).

| AC | Критерий |
|----|----------|
| AC-2.1 | ЕГЭ: выбор варианта `001`…`030` → сессия из 28 шагов |
| AC-2.2 | ОГЭ: тип 1–19 → выбор варианта → сессия из 1 шага (или несколько типов в ДЗ) |
| AC-2.3 | UI: одно задание на экран, progress bar, «Шаг N из M» |
| AC-2.4 | Кнопка «Проверить» отправляет ответ **текущего шага** и показывает верно/неверно без перезагрузки всего варианта |
| AC-2.5 | Изображения отображаются inline |
| AC-2.6 | `hint` — по кнопке «Подсказка»; не показывать автоматически |
| AC-2.7 | `detailed_explanation` — после нажатия «Проверить» (кнопка «Разбор» или авто-раскрытие) |
| AC-2.8 | Навигация «Назад» / «Далее»; итоговый экран со сводкой баллов |
| AC-2.9 | Проблемные задания скрыты |

**Проверка ответа (v1):** весь контент в БД — тестовый; `grading_mode=exact` — нормализация + сравнение с `correct_ans`. Письменные задания появятся позже и будут скрыты до v2 (§1.4).

### US-3: Домашнее задание (преподаватель → ученик)

**Как** преподаватель, **хочу** назначать ДЗ, **чтобы** контролировать подготовку.

| AC | Критерий |
|----|----------|
| AC-3.1 | Создать ДЗ: ученик(и), тип (`lecture` / `test_variant` / `test_partial`), ссылка на контент, опционально `due_at` |
| AC-3.2 | Ученик видит список активных ДЗ со статусом |
| AC-3.3 | Лекция: кнопка «Прочитано» завершает пункт ДЗ. Тест: сдача ответов по назначенным заданиям |
| AC-3.4 | `test_variant` — все задания варианта; `test_partial` — только выбранные номера `type` из указанного варианта |
| AC-3.5 | Преподаватель видит статус и результат (балл для тестов) |

### US-4: Уведомления (преподаватель)

**Как** преподаватель, **хочу** получать уведомление о сдаче ДЗ, **чтобы** не опрашивать учеников вручную.

| AC | Критерий |
|----|----------|
| AC-4.1 | При `HomeworkSubmission` создаётся `Notification` для teacher |
| AC-4.2 | UI: badge непрочитанных + список |
| AC-4.3 | Клик ведёт к карточке ученика / ДЗ |

### US-5: Управление учениками (преподаватель)

| AC | Критерий |
|----|----------|
| AC-5.1 | CRUD учеников (create минимум; deactivate опционально) |
| AC-5.2 | Назначение трека ЕГЭ/ОГЭ |

### US-6: AI-советчик (Agent + RAG) — v2+

**Как** ученик, **хочу** задавать вопросы по химии в чате, **чтобы** получать ответы на основе учебника, а не «из головы» модели.

**Как** преподаватель, **хочу** видеть диалоги учеников с советчиком, **чтобы** понимать, с чем у них затруднения.

| AC | Критерий |
|----|----------|
| AC-6.1 | Глобальный чат доступен ученику из кабинета (не только на странице лекции) |
| AC-6.2 | Ответ содержит `sources[]` — ссылки на тему/чанк или тестовый разбор |
| AC-6.3 | Агент вызывает RAG-tool перед ответом на вопросы по теории |
| AC-6.4 | При отсутствии релевантных чанков — честный отказ, без выдуманных формул |
| AC-6.5 | История сохраняется в PostgreSQL; ученик продолжает сессию по `session_id` |
| AC-6.6 | Преподаватель просматривает список сессий и transcript своих учеников |
| AC-6.7 | `correct_ans` недоступен агенту; поведение на экране теста — **TBD** (§12.6) |

---

## 8. API Surface (черновик)

| Method | Path | Role | Описание |
|--------|------|------|----------|
| POST | `/api/auth/login` | public | Вход |
| POST | `/api/auth/logout` | auth | Выход |
| GET | `/api/auth/me` | auth | Текущий пользователь |
| GET | `/api/textbook/topics` | student | Список тем |
| GET | `/api/textbook/topics/{topic}/chunks` | student | Чанки темы |
| GET | `/api/textbook/.../audio` | student | Stream OGG |
| GET | `/api/tests/variants` | student | Варианты (по треку) |
| GET | `/api/tests/variants/{ref}/questions` | student | Список вопросов (метаданные, без ответов) |
| GET | `/api/tests/images/{filename}` | student | PNG |
| POST | `/api/tests/sessions` | student | Начать сессию (вариант / partial / ДЗ) |
| GET | `/api/tests/sessions/{id}` | student | Состояние шагов, прогресс |
| POST | `/api/tests/sessions/{id}/steps/{n}/check` | student | Проверить ответ шага (Stepik «Проверить») |
| GET | `/api/tests/sessions/{id}/steps/{n}/hint` | student | Подсказка по запросу |
| POST | `/api/tests/sessions/{id}/complete` | student | Завершить сессию, итоговый score |
| GET | `/api/students` | teacher | Список учеников |
| POST | `/api/students` | teacher | Создать ученика |
| GET/POST | `/api/homework` | teacher/student | Список / создать |
| GET | `/api/homework/{id}` | both | Детали (RBAC) |
| POST | `/api/homework/{id}/submit` | student | Сдача |
| GET | `/api/notifications` | teacher | Список |
| PATCH | `/api/notifications/{id}/read` | teacher | Прочитано |
| POST | `/api/tutor/sessions` | student, teacher | Создать сессию чата (v2+) |
| GET | `/api/tutor/sessions` | student, teacher | Список своих сессий |
| GET | `/api/tutor/sessions/{id}` | student, teacher | История сообщений (RBAC) |
| POST | `/api/tutor/sessions/{id}/messages` | student, teacher | Отправить сообщение → ответ агента |
| GET | `/api/tutor/students/{id}/sessions` | teacher | Сессии ученика (read-only) |

---

## 9. UI (экраны MVP)

| Экран | Роль | Приоритет |
|-------|------|-----------|
| Login | all | P0 |
| Dashboard | student / teacher | P0 |
| Учебник: список тем | student | P0 |
| Учебник: чанк + аудио | student | P0 |
| Тесты: выбор варианта | student | P0 |
| Тесты: пошаговая сессия (Stepik UI) | student | P0 |
| Тесты: итоговая сводка сессии | student | P0 |
| Мои задания | student | P0 |
| Ученики (список) | teacher | P0 |
| Создать ДЗ (лекция / вариант / выбор заданий) | teacher | P0 |
| Уведомления | teacher | P0 |
| AI-советчик: глобальный чат | student | P2 (v2+) |
| AI-советчик: просмотр диалогов ученика | teacher | P2 (v2+) |

Дизайн-система: минимальный UI (shadcn/ui или аналог), адаптив — desktop-first, readable на планшете.

---

## 10. Риски

| Риск | Митигация |
|------|-----------|
| Большие BLOB (аудио) | Stream, не грузить в JSON; HTTP cache headers |
| Разная структура ЕГЭ vs ОГЭ | Явные enum `ExamTrack` + разные query в content repo |
| Нестандартные ответы | Начать с exact match; логировать mismatch для доработки |
| Один преподаватель — жёсткая связь | `teacher_id` на ученике; multi-tenant заложить в PK, не в UI |
| Кодировка / markdown в вопросах | UTF-8 end-to-end; markdown renderer с sanitization |
| Галлюцинации AI-советника | RAG-only ответы; цитаты; guardrail off-topic; тесты без `correct_ans` |
| Стоимость LLM API | Абстракция провайдера; mock в тестах; мониторинг токенов (post-launch) |
| Prompt injection в `lecture` | Sanitize tool output; не выполнять инструкции из контента учебника |

---

## 11. Принятые решения (ревью)

| Вопрос | Решение |
|--------|---------|
| Подсказки при тестах | `hint` — **по запросу** ученика (кнопка) |
| ДЗ «прочитать лекцию» | Достаточно кнопки **«Прочитано»** |
| Состав ДЗ по тестам | **И** целый вариант, **и** выбор отдельных номеров заданий (`type`) |
| Порядок тем учебника | **Как в БД** (порядок `MIN(rowid)` по `prepared_lectures`) |
| UX тестов | **Как Stepik:** пошагово, «Проверить», прогресс, итог |
| Письменные задания + AI | **Post-MVP (v2):** при добавлении в БД — скрыть до AI; сейчас в БД только тестовые |
| Состав контентных БД | **Только тестовые задания** (краткий ответ); письменных пока нет |
| AI-советчик | **v2+** после MVP; Agent (LangGraph) + RAG; детали в `docs/specs/tutor-rag.md` |
| RAG retrieval | Срез 2a: keyword → срез 2b: hybrid + pgvector |
| Роли в чате | Ученик + преподаватель; история в PostgreSQL, teacher read-only на учеников |
| LLM провайдер | Абстракция; конкретный vendor — до реализации |

## 12. Открытые вопросы

Ответы желательны **до** `planning-and-task-breakdown`:

1. **Пункт 3 MVP** в исходном ТЗ обозначен как «3. .» — что это за фича?
2. **Онбординг:** преподаватель задаёт пароль ученику или ученик меняет при первом входе?
3. **Деплой:** есть ли уже VPS/домен? Нужен ли HTTPS с Let's Encrypt в v1?
4. **ОГЭ картинки:** в тексте часто «на рисунке» без плейсхолдера — правило сопоставления `type` → `OGE000N.png`?
5. **`detailed_explanation`:** показывать автоматически после «Проверить» или по кнопке «Разбор»? *(в spec: после проверки шага)*
6. **AI на экране теста:** только теория / tool `get_hint` / чат отключён? *(решить на пилоте v2+)*
7. **LLM провайдер:** OpenAI / OpenRouter / локально? *(до начала §1.6 implement)*

---

## 13. Следующий шаг

После **одобрения spec** → `planning-and-task-breakdown` → `tasks/plan.md` → инкрементальная реализация по `AGENTS.md`.

---

*Changelog:*  
- 0.5 — §1.6 AI-советчик (Agent + RAG, v2+): источники, retrieval, US-6, API, `docs/specs/tutor-rag.md`.  
- 0.4 — уточнение: в БД только тестовые задания; письменные — future + скрыты до AI.  
- 0.3 — UX тестов (Stepik-style), roadmap AI-проверки письменных заданий, `TestSession` API.  
- 0.2 — решения по подсказкам, ДЗ (лекция/тест), порядку тем.  
- 0.1 — первичный draft на основе анализа `test_ege.db`, `test_oge.db`, `prepared_lectures.db`.
