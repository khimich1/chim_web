# Онбординг разработчика — chim_web

**Аудитория:** второй (и последующие) разработчики проекта  
**Обновлено:** 2026-07-13  
**Связанные документы:** [Правила разработки](./development-workflow.md) · [AGENTS.md](../AGENTS.md) · [SPEC.md](../SPEC.md) · [tasks/plan.md](../tasks/plan.md)

---

## 1. Что это за проект

**chim_web** — веб-платформа для репетитора по химии и его учеников (подготовка к **ЕГЭ** и **ОГЭ**).

| Роль | Возможности |
|------|-------------|
| **Ученик** | Учебник с аудио, пошаговые тесты (Stepik-style), ДЗ, рейтинг, AI-советчик |
| **Преподаватель** | Ученики, конструктор тем/заданий, назначение ДЗ, проверка письменных работ, уведомления, просмотр диалогов с AI |

**Стек:** FastAPI (Python 3.12) + Next.js App Router (Node 20) + PostgreSQL (pgvector) + read-only SQLite для контента.

**Язык UI:** русский.

---

## 2. Что получить от владельца проекта до старта

| Что | Зачем |
|-----|--------|
| Доступ к git-репозиторию | `main` — рабочая ветка |
| Три контентных `.db` в корень monorepo | Не в git; без них учебник и тесты пустые |
| `OPENAI_API_KEY` (опционально) | AI-советчик и hybrid RAG |
| 15-минутный sync | Текущая задача, зоны ответственности, как ревьюим PR |

### Контентные файлы (положить в корень `chim_web/`)

```
test_ege.db           # банк заданий ЕГЭ
test_oge.db           # банк заданий ОГЭ
prepared_lectures.db  # учебник: лекции, аудио, QA
```

Минимальные фикстуры только для E2E (не полный контент):

```bash
python scripts/e2e/create_content_dbs.py
```

---

## 3. Установка и первый запуск

### Требования

| Инструмент | Версия |
|------------|--------|
| Python | 3.12 |
| Node.js | 20 |
| Git | любая свежая |
| Docker Desktop | рекомендуется (PostgreSQL + pgvector, полный stack) |

### Backend

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

**Вариант A — быстрый старт (SQLite, без tutor hybrid RAG):**

В `backend/.env` оставить:

```
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
```

**Вариант B — полный стек (рекомендуется):**

```bash
# из корня репо
docker compose up -d postgres
# Windows one-shot: .\scripts\setup-local.ps1
```

В `backend/.env`:

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/chemistry
```

Миграции и демо-учитель:

```bash
cd backend
alembic upgrade head
python -m app.cli.seed_teacher --email teacher@example.com --password teacher-pass
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
```

В `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

```bash
npm run dev
```

### Проверка

| URL | Ожидание |
|-----|----------|
| http://localhost:3000 | Страница входа |
| http://localhost:8000/docs | OpenAPI |
| http://localhost:8000/health | `content_databases.*.exists: true` |

**Логин после seed:** `teacher@example.com` / `teacher-pass`

**Ученик:** создаётся только преподавателем — UI `/teacher/students` или `POST /api/students`. Self-registration нет.

### Docker (весь stack)

```bash
cp .env.example .env
docker compose up --build
```

Приложение: http://localhost:8080 (nginx → Next + FastAPI).

### AI-советчик (опционально)

В `backend/.env` добавить `OPENAI_API_KEY=...`, нужен PostgreSQL:

```bash
python -m app.cli.index_rag --rebuild
```

---

## 4. Архитектура

### Принцип

```
Frontend (Next.js)  →  только UI и вызовы API
Backend (FastAPI)   →  вся бизнес-логика
```

Слои backend: **Router → Service → Repository**.

### Два слоя данных

| Слой | Хранилище | Содержимое |
|------|-----------|------------|
| **Контент** | SQLite `.db` в корне (read-only) | Учебник, тесты ЕГЭ/ОГЭ, аудио BLOB |
| **Прикладной** | PostgreSQL | Пользователи, ДЗ, сессии, tutor, uploads, stats |

### Multi-teacher (Variant A)

Несколько преподавателей на одном инстансе. Изоляция по `teacher_id`. Provisioning:

```bash
python -m app.cli.seed_teacher --email teacher-b@example.com --password '...'
pytest tests/multi_teacher/
```

Контент SQLite и RAG — **общие** для всех. Leaderboard — **глобальный** (cross-tenant).

### Auth

- Email + пароль, роли `teacher` / `student`
- JWT в **httpOnly cookie** (`credentials: 'include'`)
- **Не** хранить токен в `localStorage`

### Структура репозитория

```
chim_web/
├── backend/app/
│   ├── main.py                 # 16 роутеров
│   ├── api/routers/            # HTTP (тонкий слой)
│   ├── schemas/                # Pydantic — контракт API
│   ├── services/               # бизнес-логика
│   │   ├── rag/                # RAG: ingestion, pgvector, retriever
│   │   ├── tutor/              # LangGraph agent, solve-pipeline
│   │   └── test_session/       # adapters: exam / homework / custom
│   ├── repositories/
│   │   ├── content/            # SQLite SELECT
│   │   └── app/                # PostgreSQL
│   ├── models/                 # SQLAlchemy ORM
│   ├── cli/                    # seed_teacher, index_rag, seed_e2e
│   └── data/textbook_sections.yaml
├── backend/alembic/versions/   # миграции 001–017
├── backend/tests/              # pytest + tutor/eval + multi_teacher/
├── frontend/app/               # /login, /student/*, /teacher/*
├── frontend/components/        # UI по доменам
├── frontend/lib/api/           # typed клиент к FastAPI
├── SPEC.md                     # спецификация (источник правды)
├── tasks/plan.md               # план задач и статусы
└── docs/                       # идеи, ADR, стратегия, specs
```

### Маршруты UI

| Путь | Кто |
|------|-----|
| `/login` | все |
| `/student/*` | учебник, тесты, ДЗ, рейтинг |
| `/teacher/*` | ученики, ДЗ, темы, уведомления, tutor |

---

## 5. Текущее состояние проекта

На момент онбординга (см. актуальный **Progress Snapshot** в `tasks/plan.md`):

| Фаза | Содержание | Статус |
|------|------------|--------|
| 0–10 | Foundation, auth, students, textbook, tests, homework | ✅ |
| 11–12 | UI redesign, step-dots, resume, таблица Менделеева | ✅ |
| 13 | Баллы, streak, leaderboard | ✅ |
| 14–15 | Конструктор заданий, проверка письменных ДЗ | ✅ (ручной QR/voice E2E — pending) |
| 16 | ЕГЭ типы 29–34 в content DB | ✅ |
| 17 | Multi-teacher, CI, RAG pg-only, Playwright E2E | ✅ |
| 18 | Учебник: скорость аудио, разделы, видео | в работе / близко к готовности |
| 9–10 | AI-советчик (v2+) | код есть; guards A2/A3 отложены |

**Уточни у владельца проекта** конкретную задачу на старт.

---

## 6. Команды на каждый день

### Backend

```bash
cd backend && .venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
pytest
pytest tests/multi_teacher/
ruff check .
mypy app/services/ app/api/
alembic upgrade head    # после pull с новыми миграциями
```

### Frontend

```bash
cd frontend
npm run dev
npm run test
npm run lint
npm run build
npm run test:e2e        # нужен поднятый stack (Docker)
```

### CLI

```bash
python -m app.cli.seed_teacher --email you@example.com --password '...'
python -m app.cli.index_rag --rebuild
python -m app.cli.seed_e2e
```

---

## 7. Что прочитать (порядок)

| # | Файл | Зачем |
|---|------|-------|
| 1 | [development-workflow.md](./development-workflow.md) | как работаем вдвоём |
| 2 | [AGENTS.md](../AGENTS.md) | команды, конвенции |
| 3 | [SPEC.md](../SPEC.md) | §1 Objective, §6 Architecture, §9 UI |
| 4 | [tasks/plan.md](../tasks/plan.md) | Progress Snapshot — что сделано / в работе |
| 5 | По задаче | `docs/specs/tutor-rag.md`, `docs/ideas/*.md` |

---

## 8. Частые проблемы

| Симптом | Решение |
|---------|---------|
| Пустой учебник/тесты | Нет `.db` в корне — запросить у владельца |
| «Бэкенд не отвечает» в UI | Проверить uvicorn :8000 и `NEXT_PUBLIC_API_URL` |
| CORS error | `CORS_ORIGINS=http://localhost:3000` в `backend/.env` |
| `alembic` падает на pgvector | PostgreSQL с pgvector: `docker compose up -d postgres` |
| Tutor не работает | `OPENAI_API_KEY` + Postgres + `index_rag --rebuild` |
| 401 после долгой работы | Access token 60 мин — перелогиниться |
| Тесты падают после pull | `pip install -r requirements.txt`, `npm ci`, `alembic upgrade head` |

---

## 9. Чеклист готовности

- [ ] Репозиторий склонирован
- [ ] Три `.db` на месте, `/health` → `exists: true`
- [ ] Backend стартует, `/docs` открывается
- [ ] Frontend на :3000, логин teacher работает
- [ ] Создан тестовый ученик, открывается учебник
- [ ] `pytest` и `npm run test` зелёные
- [ ] Прочитаны `development-workflow.md` и Progress Snapshot в `plan.md`
- [ ] Понятна первая задача и критерий «готово»

---

## 10. CI

GitHub Actions (`.github/workflows/ci.yml`):

- **backend:** ruff, mypy (services + api), pytest, coverage ≥80%
- **frontend:** eslint, vitest, openapi-typescript drift, build
- **docker-compose:** smoke через nginx :8080
- **e2e:** Playwright smoke (login → тест → submit ДЗ)

Перед merge: локально `pytest` + `npm run test` + `npm run lint`.
