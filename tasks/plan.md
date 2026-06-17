# Implementation Plan: Chemistry (chim_web) MVP

**Источник:** [SPEC.md](../SPEC.md) v0.6  
**Дата плана:** 2026-06-09  
**Обновлено:** 2026-06-17  
**Статус:** MVP ~90% + AI-советчик v2 (Tasks 31–37) в working tree; Task 38 — tutor hardening (code review round 1+2); Task 39–40 — мульти-item ДЗ (SPEC §1.7) + hardening; **Phase 11 (Tasks 48–52) — UI redesign (SPEC §14), визуальный язык по референсам, адаптив под мобилку — ⏳ pending**

---

## Overview

Веб-приложение для репетитора по химии и учеников: учебник (лекции + аудио), тесты ЕГЭ/ОГЭ в стиле Stepik, домашние задания, уведомления преподавателю. Monorepo FastAPI + Next.js; контент — read-only SQLite; прикладные данные — PostgreSQL.

**Текущее состояние репозитория (2026-06-17):**

| Слой | Состояние |
|------|-----------|
| `backend/` | FastAPI: auth, students, textbook, tests, TestSession, homework, notifications |
| `frontend/` | Next.js: login, dashboards, учебник, Stepik-тесты, ДЗ, уведомления |
| Контентные `.db` | В корне monorepo, read-only |
| Тесты | `pytest` 128 passed; `vitest` 11 passed |
| Git | Tasks 0–19 закоммичены; MVP 20–28 + tutor 31–36 — **в working tree** |

**Стратегия:** вертикальные срезы (schema → repo → service → router → frontend → тест) по приоритету P0 из spec §9.

---

## Progress Snapshot

| Task | Название | Статус | Примечание |
|------|----------|--------|------------|
| 0–3 | Foundation | ✅ done | commit `a85756d` |
| 4–5 | Auth | ✅ done | `47b9e44`, `ea3a36b` |
| 6–7 | Students | ✅ done | API + UI учеников |
| 8–10 | Textbook | ✅ done | AC-1.5 (QA self-check) — не делали |
| 11–16 | Tests backend | ✅ done | grading, catalog, images, TestSession API |
| 17–19 | Tests UI (Stepik) | ✅ done | variant picker, step view, summary |
| 20–21 | Homework models + API | 🟡 local | не в git |
| 22 | Submit lecture | 🟡 local | тест в `test_homework_api.py` |
| 23 | Submit test via session | ✅ done | `test_homework_submit_test.py` покрывает `test_variant` / `test_partial` |
| 24–25 | Homework UI | 🟡 local | create, list, submit flows, teacher results |
| 26–27 | Notifications | 🟡 local | backend + `NotificationBell` |
| 28 | Dashboards | 🟡 partial | счётчики и ссылки есть; отдельные `*Nav` — нет |
| 29 | RBAC test suite | 🟡 local | `test_rbac.py` + `test_security.py`; coverage check pending |
| 30 | Docker + CI | ⏳ pending | |
| 31 | RAG layer (keyword + Chroma) | 🟡 local | CLI `index_rag --rebuild [--chroma]` |
| 32 | LangGraph agent port | 🟡 local | `services/tutor/` from RAG_chemistry |
| 33 | PostgreSQL sessions/messages | 🟡 local | migration `004_tutor` |
| 34 | Solve-pipeline + gating | ⏳ pending | planner/critic not ported |
| 35 | Tutor API | 🟡 local | `/api/tutor/*` + mock LLM tests |
| 36 | Tutor UI overlay | 🟡 local | `TutorChatOverlay`, teacher transcript |
| 37 | Eval + deps lock | 🟡 partial | deps in requirements.txt; eval pending |
| 38 | Tutor hardening (code review) | ✅ local | `docs/specs/tutor-rag.md` §15 — round 1 (I1–I7, S1, S3, S4) + round 2 (B1–B4) закрыты; S2 (markdown в bubble) отложен как отдельный подсрез |
| 39 | Homework мульти-item submit + hardening | ✅ local | SPEC §1.7: агрегация всех items (одна `TestSession`, `variant_ref=null`), `HomeworkItemProgress`, per-item прогресс, submit при 100%; общий `homework_mapper`; tutor settings-инъекция (баг реального LLM в pytest) |
| 40 | Homework UI — конструктор выбора заданий | ✅ local | мульти-item форма, выбор `type` из разных вариантов, per-item прогресс у ученика (AC-3.6) |
| 41 | Анти-галлюцинации агента (срез 16-1) | ⏳ pending | `tutor-rag.md` §16.1 A3+A2+O1: порог retrieval, citation guard, логи tool-вызовов |
| 42 | Solve-pipeline v1.5 (срез 16-2) | ⏳ pending | `tutor-rag.md` §17: intent_router/prepare_context/validation/critic (+ planner этап B); заменяет/детализирует Task 34 |
| 43 | Персональный тьютор — student tools (срез 16-3) | ⏳ pending | §16.2: `get_my_homework`, `analyze_my_mistakes`, `recommend_topics` |
| 44 | Тренажёр + suggested prompts (срез 16-4) | ⏳ pending | §16.2/16.3: `generate_practice`, `get_selfcheck`, U3/U4 |
| 45 | Teacher-аналитика — tools (срез 16-5) | ⏳ pending | §16.2: `summarize_student`, `suggest_homework` (черновик), `class_overview` |
| 46 | Hybrid retrieval 2b + eval (срез 16-6) | ⏳ pending | §16.1 A4 + §16.4 O2: keyword∪embeddings, recall@5 ≥ 0.8 |
| 47 | UX + профиль в PostgreSQL (срез 16-7) | ⏳ pending | §16.1 A7 + §16.3 U1/U2: streaming SSE, markdown, профиль из JSON → PG |
| 48 | Design tokens + базовая тема + логотип + blobs | ⏳ pending | SPEC §14.1/14.2: палитра (teal), `globals.css`, логотип-колба, `DecorativeBlobs` |
| 49 | Редизайн страницы учебника + mobile nav | ⏳ pending | SPEC §14.2/14.5: карточка, section pill, callouts, formula chips, collapsible nav |
| 50 | Кастомный аудиоплеер | ⏳ pending | SPEC §14.2: pill-плеер вместо нативного `<audio>`, a11y/клавиатура |
| 51 | Редизайн тестов (Stepik) + test-modal + итог | ⏳ pending | SPEC §14.2/14.5: card strip, прогресс, blobs, адаптив |
| 52 | Редизайн ДЗ/дашборд/login + mobile & a11y pass | ⏳ pending | SPEC §14.5/14.6: одноколоночные карточки, focus-visible, контраст |

**Текущий этап:** Task 40 (UI-конструктор мульти-item ДЗ) — ✅ local; далее Task 29 (coverage), Task 30 (Docker/CI), Phase 10 (Tasks 41–47), **Phase 11 (Tasks 48–52, UI redesign) — можно вести параллельно, начиная с Task 48→49**.

---

## Architecture Decisions

| Решение | Обоснование |
|---------|-------------|
| Router → Service → Repository | Согласно `AGENTS.md`; бизнес-логика не в роутерах |
| Два слоя репозиториев: `repositories/content/` (SQLite SELECT) и `repositories/app/` (PostgreSQL) | Spec §6: не смешивать ORM контента с app DB |
| JWT в httpOnly cookies | Spec §3, security checklist |
| `TestSession` в app DB для Stepik-flow | Spec §1.3; один UI для свободной практики и ДЗ |
| `grading_mode=exact` в v1 | Spec §1.4; письменные скрыты до v2 |
| Первый teacher — Alembic seed / CLI | Один преподаватель на MVP; self-registration учеников нет |
| shadcn/ui + Tailwind | Spec §9; минимальный UI, desktop-first |
| CI / Docker — после первого E2E-среза | Spec §8, допущение 8 |

---

## Dependency Graph (упрощённо)

```
Task 0  Monorepo scaffold                    ✅
    │
Task 1  Config + health                      ✅
    │
Task 2  PostgreSQL models + Alembic         ✅
    │
Task 3  Content SQLite repos                 ✅
    │
    ├── Task 4–5   Auth (backend → frontend) ✅
    ├── Task 6–7   Students (teacher CRUD) ✅
    ├── Task 8–10  Textbook (API → audio → UI) ✅
    ├── Task 11–16 Tests backend (grading, catalog, TestSession) ✅
    ├── Task 17–19 TestSession UI (Stepik)   ✅
    ├── Task 20–27 Homework + notifications  🟡 local
    └── Task 28–30 Dashboards + hardening    🟡 / ⏳
```

---

## Open Questions (из SPEC §12)

План **продолжается** с дефолтами ниже. Поправь до старта Task 4+, если нужно иначе.

| # | Вопрос | Дефолт для плана |
|---|--------|------------------|
| 1 | «Пункт 3 MVP» в исходном ТЗ | Игнорируем — в SPEC v0.6 нет отдельной фичи |
| 2 | Пароль ученика при онбординге | Teacher задаёт временный пароль; смена при первом входе — **вне v1** |
| 3 | VPS / HTTPS в v1 | Dev-only до Task 30; prod Docker + Let's Encrypt — отдельная фаза |
| 4 | ОГЭ картинки без плейсхолдера | MVP: только явные `[рисунокNNNN]` / известные паттерны; маппинг `type→OGE000N` — Task 15a, если нужен |
| 5 | `detailed_explanation` | По кнопке «Разбор» после «Проверить» (не авто) |

---

## Task List

### Phase 0: Foundation

---

## Task 0: Monorepo scaffold

**Description:** Создать каркас `backend/` (FastAPI) и `frontend/` (Next.js App Router), `.gitignore`, `.env.example`, подключить контентные SQLite (пути из env). Health endpoint и пустая главная Next.

**Acceptance criteria:**
- [ ] `uvicorn app.main:app` стартует на `:8000`, `GET /health` → 200
- [ ] `npm run dev` стартует на `:3000`
- [ ] `.env.example` документирует `DATABASE_URL`, `CONTENT_*_DB_PATH`, `JWT_SECRET`, `CORS_ORIGINS`
- [ ] Контентные `.db` лежат в корне monorepo (или путь настраивается)

**Verification:**
- [ ] `cd backend && pytest` — хотя бы `test_health.py`
- [ ] `cd frontend && npm run build`
- [ ] Ручная проверка: Next показывает заглушку, FastAPI `/docs` открывается

**Dependencies:** None

**Files:**
- `backend/app/main.py`, `backend/requirements.txt`, `backend/tests/test_health.py`
- `frontend/package.json`, `frontend/app/page.tsx`, `frontend/next.config.ts`
- `.gitignore`, `backend/.env.example`, `frontend/.env.local.example`

**Scope:** M

---

## Task 1: Core config, DB session, CORS

**Description:** `pydantic-settings`, async PostgreSQL engine + `AsyncSession`, dependency `get_db`, CORS для `localhost:3000`, structured logging.

**Acceptance criteria:**
- [ ] `Settings` читает env; ошибка при отсутствии обязательных полей
- [ ] `get_db` yield/close session корректно
- [ ] CORS разрешает credentials с frontend origin

**Verification:**
- [ ] `pytest backend/tests/test_config.py`
- [ ] TestClient: preflight OPTIONS с credentials

**Dependencies:** Task 0

**Files:**
- `backend/app/core/config.py`, `backend/app/core/logging.py`
- `backend/app/db/session.py`, `backend/app/db/base.py`
- `backend/tests/test_config.py`

**Scope:** S

---

## Task 2: App DB models + Alembic initial migration

**Description:** ORM-модели: `User`, `StudentProfile` (track, teacher_id). Alembic init + первая миграция. CLI/seed для создания первого teacher.

**Acceptance criteria:**
- [ ] `alembic upgrade head` создаёт таблицы users, student_profiles
- [ ] Роли `teacher` | `student` как enum/string
- [ ] Seed-команда создаёт teacher (email + hashed password)

**Verification:**
- [ ] `pytest backend/tests/test_models.py`
- [ ] `alembic upgrade head` на чистой БД без ошибок

**Dependencies:** Task 1

**Files:**
- `backend/app/models/user.py`, `backend/app/models/student_profile.py`
- `backend/alembic/versions/001_initial.py`
- `backend/app/cli/seed_teacher.py` (или `scripts/seed.py`)
- `backend/tests/test_models.py`

**Scope:** M

---

## Task 3: Content SQLite repositories (read-only)

**Description:** Слой `repositories/content/`: подключение к трём SQLite, базовые query для lectures и tests. Только SELECT. Фильтр `has_issue=1` / `tests_bug`.

**Acceptance criteria:**
- [ ] `LectureContentRepo.list_topics()` — порядок `ORDER BY MIN(rowid)` (AC-1.1)
- [ ] `TestContentRepo` разделяет EGE/OGE по пути БД
- [ ] Проблемные задания не возвращаются (AC-2.9)

**Verification:**
- [ ] `pytest backend/tests/content/` с fixture-копией SQLite (или тестовой мини-БД)
- [ ] Unit: `list_topics` порядок, `filter_has_issue`

**Dependencies:** Task 0

**Files:**
- `backend/app/repositories/content/base.py`
- `backend/app/repositories/content/lectures.py`, `tests.py`
- `backend/tests/content/test_lectures_repo.py`, `test_tests_repo.py`

**Scope:** M

---

### Checkpoint: Foundation (после Tasks 0–3)

- [x] Backend стартует, миграции применяются
- [x] Content repos читают fixture SQLite
- [x] Frontend build зелёный
- [x] **Review с человеком:** пути к `.db`, seed teacher credentials

---

### Phase 1: Auth + RBAC

---

## Task 4: Auth backend (login, logout, me)

**Description:** JWT access token в httpOnly cookie, bcrypt passwords, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`. Dependencies: `get_current_user`, `require_teacher`, `require_student`.

**Acceptance criteria:**
- [ ] Login teacher/student → Set-Cookie httpOnly
- [ ] `/me` возвращает id, email, role, track (для student)
- [ ] Неверный пароль → 401; без cookie → 401 на protected routes
- [ ] JWT **не** в response body

**Verification:**
- [ ] `pytest backend/tests/test_auth.py`
- [ ] TestClient: login → me → logout → me 401

**Dependencies:** Task 2

**Files:**
- `backend/app/core/security.py`, `backend/app/schemas/auth.py`
- `backend/app/services/auth_service.py`, `backend/app/api/routers/auth.py`
- `backend/app/api/deps.py`
- `backend/tests/test_auth.py`

**Scope:** M

---

## Task 5: Auth frontend (login + session)

**Description:** Страница `/login`, `lib/api/client.ts` с `credentials: 'include'`, auth context/hook, redirect по роли на dashboard.

**Acceptance criteria:**
- [ ] Форма логина: email + password, ошибки 401 в UI
- [ ] После login teacher → `/(teacher)`, student → `/(student)`
- [ ] Protected layout редиректит неавторизованных на `/login`

**Verification:**
- [ ] `npm run test -- LoginForm` (vitest + MSW)
- [ ] Ручная проверка: login seed teacher в браузере

**Dependencies:** Task 4

**Files:**
- `frontend/app/(auth)/login/page.tsx`, `frontend/components/auth/LoginForm.tsx`
- `frontend/lib/api/auth.ts`, `frontend/lib/api/client.ts`
- `frontend/components/auth/LoginForm.test.tsx`

**Scope:** M

---

### Checkpoint: Auth (после Tasks 4–5)

- [x] Teacher login E2E: browser → dashboard redirect
- [x] pytest + vitest зелёные

---

### Phase 2: Student management (teacher)

---

## Task 6: Students API (teacher creates students)

**Description:** `GET /api/students`, `POST /api/students` — создание ученика с email, временным паролем, track (`ege`|`oge`). Привязка `teacher_id` из текущего teacher.

**Acceptance criteria:**
- [ ] Только teacher может создавать/листить своих учеников (AC-5.1)
- [ ] Track задаётся при создании (AC-5.2)
- [ ] Student не имеет доступа к `GET /api/students` → 403

**Verification:**
- [ ] `pytest backend/tests/test_students.py`
- [ ] Track isolation: student `oge` в профиле

**Dependencies:** Task 4

**Files:**
- `backend/app/schemas/students.py`, `backend/app/services/student_service.py`
- `backend/app/repositories/app/student_repo.py`
- `backend/app/api/routers/students.py`
- `backend/tests/test_students.py`

**Scope:** M

---

## Task 7: Students UI (teacher)

**Description:** Экран `/(teacher)/students` — список учеников, форма создания (email, пароль, track).

**Acceptance criteria:**
- [ ] Список обновляется после создания
- [ ] Track выбирается в форме (ЕГЭ / ОГЭ)
- [ ] 422/403 отображаются понятно

**Verification:**
- [ ] vitest для формы
- [ ] Ручная проверка: teacher создаёт student, student может залогиниться

**Dependencies:** Task 5, Task 6

**Files:**
- `frontend/app/(teacher)/students/page.tsx`
- `frontend/components/students/StudentList.tsx`, `CreateStudentForm.tsx`
- `frontend/lib/api/students.ts`

**Scope:** M

---

### Phase 3: Textbook (US-1)

---

## Task 8: Textbook API (topics, chunks)

**Description:** `GET /api/textbook/topics`, `GET /api/textbook/topics/{topic}/chunks`, `GET .../chunks/{idx}` — markdown `lecture`, без BLOB в JSON.

**Acceptance criteria:**
- [ ] AC-1.1, AC-1.2, AC-1.3
- [ ] `has_audio: bool` вместо отдачи `tts_audio` в JSON
- [ ] Только student role

**Verification:**
- [ ] `pytest backend/tests/test_textbook.py`

**Dependencies:** Task 3, Task 4

**Files:**
- `backend/app/schemas/textbook.py`, `backend/app/services/textbook_service.py`
- `backend/app/api/routers/textbook.py`
- `backend/tests/test_textbook.py`

**Scope:** M

---

## Task 9: Textbook audio streaming

**Description:** `GET /api/textbook/topics/{topic}/chunks/{idx}/audio` — stream `audio/ogg`, cache headers.

**Acceptance criteria:**
- [ ] AC-1.4: корректный Content-Type, streaming без загрузки всего файла в память (chunked)
- [ ] 404 для чанка без аудио

**Verification:**
- [ ] `pytest backend/tests/test_textbook_audio.py`
- [ ] Ручная проверка: `<audio>` воспроизводит в браузере

**Dependencies:** Task 8

**Files:**
- `backend/app/api/routers/textbook.py` (audio route)
- `backend/tests/test_textbook_audio.py`

**Scope:** S

---

## Task 10: Textbook UI

**Description:** Список тем, страница темы с чанками, просмотр чанка (markdown renderer + audio player). Опционально: QA self-check (AC-1.5) — если останется время, отдельным XS-task.

**Acceptance criteria:**
- [ ] AC-1.1–AC-1.4 в UI
- [ ] Markdown sanitized (XSS-safe renderer)
- [ ] Навигация между чанками темы

**Verification:**
- [ ] vitest: markdown chunk render
- [ ] Ручная проверка: student открывает «Алканы», чанк 0, аудио играет

**Dependencies:** Task 5, Task 8, Task 9

**Files:**
- `frontend/app/(student)/textbook/page.tsx`
- `frontend/app/(student)/textbook/[topic]/page.tsx`
- `frontend/components/textbook/ChunkViewer.tsx`, `TopicList.tsx`
- `frontend/lib/api/textbook.ts`

**Scope:** M

---

### Checkpoint: Textbook (после Tasks 8–10)

- [x] Success criterion: ученик ЕГЭ видит темы и чанк с аудио
- [x] pytest + vitest зелёные
- [ ] AC-1.5 QA self-check — отложено

---

### Phase 4: Tests — content & grading (US-2, часть 1)

---

## Task 11: Answer grading service

**Description:** `GradingService` с `grading_mode=exact`: нормализация ответа (trim, пробелы, регистр где уместно) + сравнение с `correct_ans`.

**Acceptance criteria:**
- [ ] Типовые ответы `23`, `422` проходят после нормализации
- [ ] Mismatch логируется (для будущей доработки, spec §10)
- [ ] Unit-тесты на edge cases (пустой ответ, лишние пробелы)

**Verification:**
- [ ] `pytest backend/tests/test_grading.py`

**Dependencies:** Task 3

**Files:**
- `backend/app/services/grading_service.py`
- `backend/tests/test_grading.py`

**Scope:** S

---

## Task 12: Tests API — variants & questions

**Description:** `GET /api/tests/variants` (по track студента), `GET /api/tests/variants/{ref}/questions` — метаданные без `correct_ans`, `hint`, `detailed_explanation`.

**Acceptance criteria:**
- [ ] AC-2.1 (EGE 001–030), AC-2.2 (OGE по типам)
- [ ] Track isolation: `oge` student не видит EGE variants (success criterion)
- [ ] `has_issue` скрыты

**Verification:**
- [ ] `pytest backend/tests/test_tests_api.py`

**Dependencies:** Task 3, Task 4, Task 11

**Files:**
- `backend/app/schemas/tests.py`, `backend/app/services/test_catalog_service.py`
- `backend/app/api/routers/tests.py`
- `backend/tests/test_tests_api.py`

**Scope:** M

---

## Task 13: Test images API + question text substitution

**Description:** `GET /api/tests/images/{filename}` — PNG из content DB. Сервис замены `[рисунокNNNN]` на `<img src="...">` или image URL в API response.

**Acceptance criteria:**
- [ ] AC-2.5: плейсхолдеры заменены на URL images endpoint
- [ ] EGE: `рисунок0001` → корректный файл
- [ ] OGE: явные плейсхолдеры работают

**Verification:**
- [ ] `pytest backend/tests/test_test_images.py`

**Dependencies:** Task 12

**Files:**
- `backend/app/services/image_substitution.py`
- `backend/app/api/routers/tests.py` (images route)
- `backend/tests/test_test_images.py`

**Scope:** M

---

## Task 14: TestSession models + migration

**Description:** ORM: `TestSession`, `TestSessionStep` (test_id, answer, is_correct, hint_used, status). Alembic migration.

**Acceptance criteria:**
- [ ] Модель соответствует spec §3 (steps, homework_assignment_id nullable)
- [ ] Статусы шага: `unseen` | `answered` | `checked`

**Verification:**
- [ ] `pytest backend/tests/test_test_session_models.py`
- [ ] `alembic upgrade head`

**Dependencies:** Task 2

**Files:**
- `backend/app/models/test_session.py`
- `backend/alembic/versions/002_test_sessions.py`
- `backend/tests/test_test_session_models.py`

**Scope:** S

---

## Task 15: TestSession API — create, get, check step, hint

**Description:** `POST /api/tests/sessions`, `GET /api/tests/sessions/{id}`, `POST .../steps/{n}/check`, `GET .../steps/{n}/hint`.

**Acceptance criteria:**
- [ ] AC-2.4: check возвращает `{ correct, ... }` без полного reload
- [ ] AC-2.6: hint только по отдельному GET (не в questions list)
- [ ] Повторная проверка шага обновляет ответ (spec §1.3)
- [ ] RBAC: только владелец session

**Verification:**
- [ ] `pytest backend/tests/test_test_sessions.py`

**Dependencies:** Task 11, Task 12, Task 14

**Files:**
- `backend/app/schemas/test_session.py`, `backend/app/services/test_session_service.py`
- `backend/app/repositories/app/test_session_repo.py`
- `backend/app/api/routers/test_sessions.py`
- `backend/tests/test_test_sessions.py`

**Scope:** M

---

## Task 16: TestSession API — complete + summary

**Description:** `POST /api/tests/sessions/{id}/complete` — итог score/max, детали по шагам.

**Acceptance criteria:**
- [ ] AC-2.8: итоговая сводка с баллом и статусом каждого шага
- [ ] Сессия переходит в terminal status

**Verification:**
- [ ] `pytest backend/tests/test_test_sessions_complete.py`

**Dependencies:** Task 15

**Files:**
- `backend/app/api/routers/test_sessions.py` (complete)
- `backend/tests/test_test_sessions_complete.py`

**Scope:** S

---

### Phase 5: Tests UI — Stepik-style (US-2, часть 2)

---

## Task 17: Tests UI — variant picker

**Description:** `/(student)/tests` — выбор варианта по track (EGE list / OGE by type).

**Acceptance criteria:**
- [ ] AC-2.1, AC-2.2 в UI
- [ ] Кнопка «Начать» создаёт session и редиректит на шаг 1

**Verification:**
- [ ] vitest + MSW
- [ ] Ручная проверка: создание сессии

**Dependencies:** Task 5, Task 12, Task 15

**Files:**
- `frontend/app/(student)/tests/page.tsx`
- `frontend/components/tests/VariantPicker.tsx`
- `frontend/lib/api/tests.ts`

**Scope:** M

---

## Task 18: Tests UI — step view (Stepik)

**Description:** `/(student)/tests/sessions/[id]` — одно задание на экран, progress bar, «Проверить», «Подсказка», «Разбор», «Назад»/«Далее».

**Acceptance criteria:**
- [ ] AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7
- [ ] Instant feedback без full page reload
- [ ] Images inline

**Verification:**
- [ ] vitest: StepView interactions
- [ ] Ручная проверка полного прохождения 3+ шагов

**Dependencies:** Task 13, Task 15, Task 17

**Files:**
- `frontend/app/(student)/tests/sessions/[id]/page.tsx`
- `frontend/components/tests/StepView.tsx`, `ProgressBar.tsx`, `AnswerInput.tsx`
- `frontend/components/tests/StepView.test.tsx`

**Scope:** M

---

## Task 19: Tests UI — session summary

**Description:** Экран итога после complete — score, список шагов верно/неверно.

**Acceptance criteria:**
- [ ] AC-2.8 в UI
- [ ] Кнопка «К списку тестов» / «К заданиям»

**Verification:**
- [ ] vitest + ручная проверка после complete

**Dependencies:** Task 16, Task 18

**Files:**
- `frontend/components/tests/SessionSummary.tsx`
- `frontend/app/(student)/tests/sessions/[id]/summary/page.tsx`

**Scope:** S

---

### Checkpoint: Tests (после Tasks 11–19)

- [x] Success criteria: пошаговый тест с hint по запросу, итоговая сводка
- [x] Track isolation проверен
- [x] pytest + vitest зелёные
- [x] **Review:** UX Stepik, нормализация ответов

---

### Phase 6: Homework (US-3)

---

## Task 20: Homework models + migration

> **Статус:** 🟡 реализовано локально, не закоммичено

**Description:** `HomeworkAssignment`, items JSON (`lecture` | `test_variant` | `test_partial`), `HomeworkSubmission`, статусы.

**Acceptance criteria:**
- [ ] Схема items соответствует spec §3
- [ ] `due_at` nullable

**Verification:**
- [ ] `pytest backend/tests/test_homework_models.py`
- [ ] `alembic upgrade head`

**Dependencies:** Task 2, Task 14

**Files:**
- `backend/app/models/homework.py`
- `backend/alembic/versions/003_homework_and_notifications.py`
- `backend/tests/test_homework_models.py`

**Scope:** S

---

## Task 21: Homework API — teacher assign, lists, details

**Description:** `POST /api/homework` (teacher), `GET /api/homework` (role-based list), `GET /api/homework/{id}` с RBAC.

**Acceptance criteria:**
- [ ] AC-3.1, AC-3.2
- [ ] `test_variant` и `test_partial` (AC-3.4)
- [ ] Student не видит чужое ДЗ → 403

**Verification:**
- [ ] `pytest backend/tests/test_homework_api.py`

**Dependencies:** Task 6, Task 20

**Files:**
- `backend/app/schemas/homework.py`, `backend/app/services/homework_service.py`
- `backend/app/repositories/app/homework_repo.py`
- `backend/app/api/routers/homework.py`
- `backend/tests/test_homework_api.py`

**Scope:** M

---

## Task 22: Homework submit — lecture «Прочитано»

> **Статус:** 🟡 реализовано; тест в `test_homework_api.py` (отдельный файл не создавался)

**Description:** `POST /api/homework/{id}/submit` для item kind `lecture` — отметка прочитано, статус submitted.

**Acceptance criteria:**
- [ ] AC-3.3 для lecture
- [ ] Повторная сдача идемпотентна или 409 — зафиксировать в тесте

**Verification:**
- [x] `pytest backend/tests/test_homework_api.py` (`test_student_submits_lecture_homework`)

**Dependencies:** Task 21

**Files:**
- `backend/app/services/homework_submit_service.py`
- `backend/tests/test_homework_api.py` (submit lecture)

**Scope:** S

---

## Task 23: Homework submit — test via TestSession

> **Статус:** ✅ реализовано и покрыто pytest

**Description:** Связь ДЗ `test_variant`/`test_partial` с `TestSession`; submit после `complete`; score в submission.

**Acceptance criteria:**
- [x] AC-3.3, AC-3.4, AC-3.5 (частично — результат для teacher в Task 25)
- [x] Partial: только выбранные `type` из варианта

**Verification:**
- [x] `pytest backend/tests/test_homework_submit_test.py`

**Dependencies:** Task 16, Task 21

**Files:**
- `backend/app/services/homework_submit_service.py` (extend)
- `backend/tests/test_homework_submit_test.py`

**Scope:** M

---

## Task 24: Homework UI — teacher create + student list

> **Примечание (v0.6.2):** базовая форма создаёт ДЗ; полноценный **мульти-item конструктор** (несколько заданий из разных вариантов, SPEC §1.7) вынесен в Task 40.

**Description:** Teacher: форма создания ДЗ (ученик, тип, контент picker). Student: `/(student)/homework` — список со статусами.

**Acceptance criteria:**
- [ ] AC-3.1, AC-3.2 в UI
- [ ] Student открывает ДЗ → lecture chunk или test session

**Verification:**
- [ ] vitest + ручная проверка assign → student sees

**Dependencies:** Task 7, Task 10, Task 17, Task 21

**Files:**
- `frontend/app/(teacher)/homework/new/page.tsx`
- `frontend/app/(student)/homework/page.tsx`
- `frontend/components/homework/HomeworkForm.tsx`, `HomeworkList.tsx`
- `frontend/lib/api/homework.ts`

**Scope:** M

---

## Task 25: Homework UI — submit flows + teacher results

**Description:** Student: «Прочитано» на лекции; тест — редирект в session. Teacher: статус и балл в карточке ученика/ДЗ.

**Acceptance criteria:**
- [ ] AC-3.3, AC-3.5 в UI
- [ ] Teacher видит score после сдачи тестового ДЗ

**Verification:**
- [ ] Ручная проверка full flow: assign → do → teacher sees result

**Dependencies:** Task 22, Task 23, Task 24

**Files:**
- `frontend/components/homework/LectureHomework.tsx`
- `frontend/app/(teacher)/homework/[id]/page.tsx`

**Scope:** M

---

### Phase 7: Notifications (US-4)

---

## Task 26: Notifications backend

**Description:** Модель `Notification`, создание при `HomeworkSubmission`. `GET /api/notifications`, `PATCH /api/notifications/{id}/read`.

**Acceptance criteria:**
- [ ] AC-4.1
- [ ] Только teacher получает уведомления о своих учениках

**Verification:**
- [ ] `pytest backend/tests/test_notifications.py`

**Dependencies:** Task 22, Task 23

**Files:**
- `backend/app/models/notification.py`
- `backend/alembic/versions/004_notifications.py`
- `backend/app/api/routers/notifications.py`
- `backend/app/services/notification_service.py`
- `backend/tests/test_notifications.py`

**Scope:** M

---

## Task 27: Notifications UI (teacher)

**Description:** Колокольчик с badge, список, mark read, клик → карточка ДЗ/ученика.

**Acceptance criteria:**
- [ ] AC-4.2, AC-4.3

**Verification:**
- [ ] vitest + ручная проверка после submit ДЗ

**Dependencies:** Task 25, Task 26

**Files:**
- `frontend/app/(teacher)/notifications/page.tsx`
- `frontend/components/notifications/NotificationBell.tsx`
- `frontend/lib/api/notifications.ts`

**Scope:** M

---

### Checkpoint: MVP Core (после Tasks 20–27)

- [ ] Все success criteria из SPEC §1 (кроме CI/Docker) — **код есть, E2E не прогнан**
- [ ] Full flow: teacher creates student → assigns HW → student submits → notification — **нужна ручная проверка**
- [x] pytest + vitest зелёные (на закоммиченном + локальном коде)
- [ ] **Review с человеком перед polish**
- [ ] Закоммитить Tasks 20–27
- [x] Task 23: pytest на submit тестового ДЗ (`test_variant` / `test_partial`)

---

### Phase 8: Dashboards & Hardening

---

## Task 28: Dashboards (student + teacher)

> **Статус:** 🟡 базовые dashboards на `/student` и `/teacher` есть; отдельные `StudentNav`/`TeacherNav` не выделены

**Description:** P0 dashboard: краткие ссылки на учебник, тесты, задания / ученики, ДЗ, уведомления.

**Acceptance criteria:**
- [ ] Student dashboard: активные ДЗ, быстрый вход в учебник/тесты
- [ ] Teacher dashboard: счётчики (ученики, непрочитанные уведомления)

**Verification:**
- [ ] Ручная проверка навигации

**Dependencies:** Task 5, Task 24, Task 27

**Files:**
- `frontend/app/(student)/page.tsx`, `frontend/app/(teacher)/page.tsx`
- `frontend/components/layout/StudentNav.tsx`, `TeacherNav.tsx`

**Scope:** M

---

## Task 29: RBAC & security test suite

> **Статус:** 🟡 тесты добавлены локально; coverage check pending

**Description:** Интеграционные тесты: 403 cross-user, track isolation, content DB read-only guard, cookie flags.

**Acceptance criteria:**
- [x] Spec §5 testing strategy пункты 1–5 покрыты
- [x] Нет утечки `correct_ans` / hint в catalog API

**Verification:**
- [x] `pytest backend/tests/test_rbac.py`
- [x] `pytest backend/tests/test_security.py`
- [ ] `pytest --cov=app` ≥80% на auth, homework, test_sessions, notifications

**Dependencies:** Task 27

**Files:**
- `backend/tests/test_rbac.py`, `backend/tests/test_security.py`

**Scope:** M

---

## Task 30: Docker Compose + CI (post-MVP slice)

> **Статус:** ⏳ pending

**Description:** `docker-compose.yml` (nginx, next, fastapi, postgres), GitHub Actions: ruff, pytest, frontend lint+build.

**Acceptance criteria:**
- [ ] `docker compose up` поднимает stack
- [ ] CI green on push

**Verification:**
- [ ] Local `docker compose up --build`
- [ ] CI run green

**Dependencies:** Task 29

**Files:**
- `docker-compose.yml`, `Dockerfile` (backend, frontend)
- `.github/workflows/ci.yml`

**Scope:** M

---

### Checkpoint: Complete

- [ ] Все acceptance criteria SPEC §7 (US-1…US-5) — US-3/US-4 ждут финальной верификации
- [x] `pytest` + `vitest` зелёные
- [ ] `npm run build` — проверить перед merge
- [ ] Task 29 coverage check
- [ ] Task 30 Docker + CI
- [ ] Готово к code review (`code-review-and-quality`)
- [ ] ADR по content SQLite vs PostgreSQL — опционально (`documentation-and-adrs`)

---

## Parallelization Opportunities

| Параллельно (после checkpoint) | Последовательно |
|-------------------------------|-----------------|
| Task 10 UI + Task 11 grading (разные агенты) | Auth перед всем protected API |
| Task 17 UI + Task 16 complete API | Migrations перед models consumers |
| Task 28 dashboards + Task 29 tests | Homework submit после TestSession |

**Контракт-first:** перед параллелью backend/frontend на одной фиче — зафиксировать Pydantic schemas / OpenAPI fragment.

---

## Risks and Mitigations

| Риск | Impact | Mitigation | Task |
|------|--------|------------|------|
| Контентные `.db` отсутствуют в repo | High | Добавить в `.gitignore` + README с путём; fixture для CI | 0, 3 |
| BLOB audio memory | Med | StreamingResponse, не JSON | 9 |
| ЕГЭ vs ОГЭ разная структура | Med | `ExamTrack` enum, отдельные query | 3, 12 |
| Нестандартные `correct_ans` | Med | Grading + лог mismatch | 11 |
| OGE images без плейсхолдера | Med | Task 13 MVP; расширение — отдельный spike | 13 |
| Задачи L+ | Med | План уже разбит на S/M | — |

---

## Summary: порядок реализации (quick reference)

```
0 → 1 → 2 → 3 → [checkpoint]
4 → 5 → [checkpoint]
6 → 7
8 → 9 → 10 → [checkpoint]
11 → 12 → 13 → 14 → 15 → 16
17 → 18 → 19 → [checkpoint]
20 → 21 → 22 → 23 → 24 → 25
26 → 27 → [checkpoint MVP]
28 → 29 → 30 → [complete MVP]
31 → 32 → 33 → 34 → 35 → 36 → 37 → 38 → [AI-советчик v2+]
39 → 40 (мульти-item ДЗ; backend 39, затем UI 40; 39 можно параллельно с 38)
41 → 42 → 43 → 44 → 45 → 46 → 47 (надёжность и расширение агента; §16/§17)
48 → 49 → 50 → 51 → 52 (UI redesign §14; можно параллельно; начать с 48→49)
```

**Оценка:** ~30 задач MVP + 8 задач AI-советчика (v2+, Tasks 31–38) + Tasks 39–40 (мульти-item ДЗ) + Tasks 41–47 (надёжность и расширение агента, v0.7) + Tasks 48–52 (UI redesign §14, кабинет ученика, адаптив).

**Прогресс на 2026-06-17:** Tasks 0–19 ✅ | Tasks 20–28 🟡 | Tasks 29–30 ⏳ | Tasks 31–37 🟡 (v2+, в working tree) | Task 38 ✅ local | Task 39 ✅ local | Task 40 ✅ local | Tasks 41–47 ⏳

---

## Phase 9: AI-советчик (v2+) — адаптация `RAG_chemistry`

> Источник: `SPEC.md` §1.6, §11 (допущение 13), US-6, `docs/specs/tutor-rag.md` §14.
> **Только после MVP (Tasks 0–30).** Движок — портированный `RAG_chemistry`, а не разработка с нуля.
> Сквозной гейт: MVP-тесты (Tasks 0–29) остаются зелёными; реальный LLM в `pytest` не вызывается (mock).

## Task 31: Порт RAG-слоя (ingestion + retriever + Chroma) с track-метаданными

**Description:** Перенести `RAG_chemistry/app/services/rag/*` в `backend/app/services/rag/`. Индексировать `prepared_lectures` по обоим трекам; `track`, `topic`, `chunk_idx`, `chunk_title` в metadata. CLI индексации.

**Acceptance criteria:**
- [ ] `python -m app.cli.index_rag --rebuild` строит Chroma-индекс (~185 чанков) идемпотентно
- [ ] `Retriever.search(query, track=...)` фильтрует по треку; `correct_ans`/BLOB не индексируются
- [ ] Эмбеддинги через абстракцию провайдера; сеть мокается в unit

**Verification:**
- [ ] `pytest backend/tests/tutor/test_retriever.py` (mock embeddings) — релевантная тема в top-3
**Dependencies:** Task 3
**Files:** `backend/app/services/rag/{ingestion,embeddings,vectorstore,retriever}.py`, `backend/app/cli/index_rag.py`, `backend/tests/tutor/test_retriever.py`
**Scope:** M

---

## Task 32: Порт tutor-агента (graph, tools, prompts, guardrails) + RBAC + track

**Description:** Перенести `agents/chemistry/{graph,tools,prompts,guardrails}.py` в `backend/app/services/tutor/`. Tools получают `user` + `track`; RBAC student/teacher.

**Acceptance criteria:**
- [ ] Граф компилируется; топология `input_guard → agent ⇄ tools → tool_output_guard → END`
- [ ] `retrieve_theory` фильтрует по треку ученика; off-topic/injection guardrails работают
- [ ] LLM-провайдер через абстракцию (`docs/specs/tutor-rag.md` §8)

**Verification:**
- [ ] `pytest backend/tests/tutor/test_graph.py` (mock LLM): routing tools/END, guardrails
**Dependencies:** Task 31
**Files:** `backend/app/services/tutor/{graph,tools,prompts,guards}.py`, `backend/tests/tutor/test_graph.py`
**Scope:** L

---

## Task 33: Память в PostgreSQL — профиль + tutor_sessions/messages

**Description:** Заменить JSON-профиль и единоличный `MemorySaver` на PostgreSQL. Модели `TutorSession`, `TutorMessage`; профиль ученика в app DB. `save_user_info` пишет по `user_id`.

**Acceptance criteria:**
- [ ] Alembic-миграция `tutor_sessions`, `tutor_messages` (sources jsonb, page_context jsonb)
- [ ] История восстанавливается по `session_id`; изоляция по `user_id`
- [ ] `save_user_info(user, key, value)` обновляет профиль ученика в БД

**Verification:**
- [ ] `pytest backend/tests/tutor/test_memory.py`; `alembic upgrade head`
**Dependencies:** Task 2, Task 32
**Files:** `backend/app/models/tutor.py`, `backend/app/repositories/app/tutor.py`, `backend/alembic/versions/005_tutor.py`, `backend/tests/tutor/test_memory.py`
**Scope:** M

---

## Task 34: Порт solve-pipeline v1.5 + gating по TestSession

> **Статус:** ⏳ pending. **Детализирован и заменён Task 42** (срез 16-2, `tutor-rag.md` §17).
> Сохранён здесь как исторический контекст Phase 9; реализацию вести по Task 42.

**Description:** Перенести `planner/solver/critic/task_flow/state` и `validation.py`. `intent_router` направляет «разбери задание N» в solve-ветку **только вне активной тест-сессии**; иначе — теория.

**Acceptance criteria:**
- [ ] Вне теста: разбор задания → ключ сверяется кодом с `correct_ans`, есть цитата учебника
- [ ] Во время активной `TestSession` ученика: solve-ветка и `get_task` с `correct_ans` отключены
- [ ] Лимит ретраев ≤2; гибридный финал при провале

**Verification:**
- [ ] `pytest backend/tests/tutor/test_solve.py` (mock LLM): gating + routing критика
**Dependencies:** Task 32, Task 14 (TestSession), Task 33
**Files:** `backend/app/services/tutor/solve/{planner,solver,critic,task_flow,state}.py`, `backend/app/services/tutor/tasks.py`, `backend/app/services/tutor/validation.py`, `backend/tests/tutor/test_solve.py`
**Scope:** L

---

## Task 35: tutor API router + LLM-провайдер абстракция

**Description:** `POST/GET /api/tutor/sessions`, `GET /api/tutor/sessions/{id}`, `POST .../messages`, `GET /api/tutor/students/{id}/sessions` (teacher, RBAC). `page_context` принимается от overlay-окна.

**Acceptance criteria:**
- [ ] Ответ содержит `sources[]`; контекст страницы кладётся в сессию
- [ ] `page_context` сериализуется через `model_dump(mode="json")` (UUID → string) — Prove-It: `test_create_session_serializes_test_session_id_in_page_context`
- [ ] Teacher не читает сессии чужих учеников → 403
- [ ] LLM-провайдер инъектируется (mock в тестах)
- [ ] `send_message`: проверка LLM **до** персистенции user-msg; явный `rollback` при 503
- [ ] `send_message`: `asyncio.to_thread(graph.invoke)` + configurable timeout (`tutor_invoke_timeout`)
- [ ] `send_message`: двухфазный commit — не держать DB-транзакцию на время LLM (см. `docs/specs/tutor-rag.md` §5, §15 I2–I5)

**Verification:**
- [ ] `pytest backend/tests/tutor/test_tutor_api.py` (mock LLM, фиксированные tool_calls)
- [ ] `test_send_message_without_openai_key_returns_503` + assert: user-msg не в БД после 503
**Dependencies:** Task 33, Task 34
**Files:** `backend/app/api/routers/tutor.py`, `backend/app/schemas/tutor.py`, `backend/app/services/tutor_service.py`, `backend/app/core/config.py`, `backend/tests/tutor/test_tutor_api.py`
**Scope:** M

**Code review gaps (2026-06-17):** I2–I5, I7 → Task 38 или доработка в рамках 35.

---

## Task 36: Frontend — плавающее окно TutorChat (overlay) + teacher transcript

**Description:** Overlay-панель чата поверх учебника и тестов (drawer/floating window), вызывается кнопкой с любого экрана кабинета. Передаёт `page_context`. Teacher: просмотр transcript ученика.

**Acceptance criteria:**
- [ ] Окно открывается поверх `textbook`/`tests`, сворачивается, не блокирует прохождение теста
- [ ] `sources` — кликабельные ссылки; markdown sanitized
- [ ] Контекст текущей страницы (тема/активный тест) уходит в API
- [ ] При смене `pathname` — актуальный `page_context` (сброс/новая сессия, см. §15 I1)
- [ ] Loading UX: индикатор при `handleOpen` + при `handleSend`; кнопка disabled на время открытия
- [ ] `aria-live="polite"` на индикаторе загрузки
- [ ] Teacher видит список сессий ученика и transcript (read-only)

**Verification:**
- [ ] vitest: TutorChat overlay (open, send, error rollback); ручная проверка overlay поверх учебника и теста
**Dependencies:** Task 35, Task 10, Task 18
**Files:** `frontend/components/tutor/{TutorChatOverlay,SourceCitation}.tsx`, `frontend/app/teacher/tutor/page.tsx`, `frontend/lib/api/tutor.ts`
**Scope:** L

**Code review gaps (2026-06-17):** I1, I6, S1–S2, S4 → Task 38 или доработка в рамках 36.

---

## Task 37: Слияние конфигов/зависимостей + eval

**Description:** Слить `RAG_chemistry/core/config.py` в `backend/app/core/config.py` (префиксы `LLM_*`, `RAG_*`, `CHROMA_*`); добавить зависимости в `requirements.txt` (Ask first); eval-набор recall@5.

**Acceptance criteria:**
- [ ] `langgraph`, `langchain-*`, `chromadb` зафиксированы; конфликтов со стеком backend нет
- [ ] Eval: 8/10 эталонных вопросов → ожидаемый чанк в top-3 (recall@5 ≥ 0.8)
- [ ] `.env.example` дополнен `LLM_*`/`RAG_*`

**Verification:**
- [ ] `pytest backend/tests/tutor/` зелёный (без реального LLM); eval-прогон задокументирован
**Dependencies:** Task 31–36
**Files:** `backend/app/core/config.py`, `backend/requirements.txt`, `backend/.env.example`, `backend/tests/tutor/eval/*`
**Scope:** M

---

## Task 38: Tutor hardening — code review follow-up (2026-06-17)

> Источник: `docs/specs/tutor-rag.md` §15. Закрывает Important/Suggestion из ревью `TutorChatOverlay` + `send_message`.

**Description:** Доработки backend и frontend после первого среза Tasks 35–36: транзакции, таймауты, UX загрузки, актуальный `page_context`, регрессионные тесты.

**Acceptance criteria (backend):**
- [x] I2: `send_message` — commit user-msg до invoke; assistant в отдельной транзакции
- [x] I3: проверка `OPENAI_API_KEY` до `add_message`; явный `rollback` при 503
- [x] I4: `asyncio.wait_for(to_thread(...), timeout=settings.tutor_invoke_timeout)`; timeout → 504 с понятным `detail`
- [x] I5: разные `detail` для: нет ключа / таймаут / ошибка агента
- [x] I7: `test_send_message_without_openai_key_returns_503` — assert 0 user messages в сессии
- [x] S3: `sources` → `model_dump(mode="json")`

**Acceptance criteria (backend, round 2 — обзор проекта, §15):**
- [x] B1: история из PostgreSQL реплеится в граф (stateless граф, `_history_to_lc_messages`; `MemorySaver` убран)
- [x] B2: порядок transcript гарантирован relationship `order_by` + `list_messages` для replay; тест `test_session_transcript_ordered_by_created_at`
- [x] B3: off-topic guard на каждое сообщение (убрано условие `has_history`)
- [x] B4: `GET /api/tutor/health/tutor` под `CurrentUser` (не публичный)

**Acceptance criteria (frontend):**
- [x] I1: сброс `sessionId` при смене `pathname` (render-time reset, паттерн «adjust state on prop change»)
- [x] I6: state `opening`; disable кнопки «AI-советчик» и spinner при `handleOpen`
- [x] S1: `aria-live="polite"` на loading-индикаторе
- [ ] S2: markdown render + sanitization в `MessageBubble` — **отложено** (отдельный подсрез; сейчас `whitespace-pre-wrap` plain text)

**Verification:**
- [x] `pytest backend/tests/tutor/` — 35 passed (вкл. `test_tutor_health_requires_auth`, `test_session_transcript_ordered_by_created_at`, `test_multi_turn_history_replayed_into_agent`, `test_send_message_agent_error_returns_503_and_rolls_back`); полный backend — 135 passed
- [x] `npm run test` — vitest `TutorChatOverlay.test.tsx` (open, send, error rollback, pathname → new session); полный — 15 passed
- [ ] Ручная проверка: навигация учебник → тест с открытым чатом — контекст обновляется
**Dependencies:** Task 35, Task 36
**Files:** `backend/app/services/tutor_service.py`, `backend/app/services/tutor/{memory,guards}.py`, `backend/app/repositories/app/tutor_repo.py`, `backend/app/api/routers/tutor.py`, `backend/app/core/config.py`, `backend/tests/tutor/test_tutor_api.py`, `frontend/components/tutor/TutorChatOverlay.tsx`
**Scope:** M → L (с round 2)

---

## Task 39: Homework мульти-item submit + hardening (2026-06-17)

> Источник: решение SPEC §1.7 (v0.6.2) — ДЗ из нескольких items, тестовые из разных вариантов. + code review round 2 (типобезопасность). Область — MVP (Phase 6).

**Description:** Переписать `homework_submit_service` с обработки только `items[0]` на **агрегацию всех items**. Тестовые пункты из разных вариантов собираются в один `TestSession` (`variant_ref=null`, агрегированный `test_ids[]`); лекции — отдельные отметки «Прочитано». Статус/score — агрегат; `submitted` только при выполнении всех пунктов. Заодно закрыть find-ы ревью (импорт, пустой список).

**Решение (v0.6.2, реализовано):** один общий `TestSession` (`variant_ref=null`,
агрегированный `test_ids[]`); per-item прогресс в таблице `HomeworkItemProgress`;
submit авто-подтверждает лекции и требует завершённую тест-сессию для тестовых
items (gate 100%); отдельный `POST /api/homework/{id}/items/{index}/complete` для
инкрементальной отметки лекции «Прочитано».

**Acceptance criteria:**
- [x] `submit` обрабатывает **все** `items` ДЗ, а не только `items[0]`
- [x] Тестовые items из разных вариантов → один `TestSession` с агрегированным `test_ids[]` (`variant_ref=null` при нескольких вариантах)
- [x] `submitted` выставляется только когда выполнены **все** пункты (лекции + тестовая сессия `completed`); иначе `in_progress` с прогрессом
- [x] Агрегированный `score`/`max_score` из общей тест-сессии; одно уведомление преподавателю при полной сдаче (AC-3.7)
- [x] Пустой `items` не вызывает `IndexError` → 422 (guard; создание ограничено `min_length=1`)
- [~] Трек фиксируется по ученику; тестовые items резолвятся против БД трека ученика при создании сессии (явная валидация смешивания треков не нужна — items ссылаются только на имя варианта)
- [x] `HomeworkRead` импортирован в `homework_submit_service.py` (из `app.schemas.homework`)
- [x] Приватный `_to_homework_read` вынесен в общий модуль `app/services/homework_mapper.py` (`to_homework_read`)

**Verification:**
- [x] `pytest backend/tests/test_homework_submit_test.py` — 7 passed (мульти-item lecture + 2 test_partial из разных вариантов, частичный прогресс, lecture-only, complete на test-item → 422)
- [x] Полный `pytest` — 139 passed (вкл. починенный `test_send_message_without_openai_key_returns_503`)
- [x] `alembic upgrade head` / `downgrade base` — миграция `005_hw_progress` (таблица + nullable `variant_ref`) применяется и откатывается
- [ ] `mypy app/` — mypy не установлен в venv; не запускался (новые зависимости — Ask first)

**Dependencies:** Task 21, Task 23
**Files (реализовано):** `backend/app/services/homework_submit_service.py` (rewrite + `complete_item`), `backend/app/services/homework_service.py`, `backend/app/services/homework_mapper.py` (new), `backend/app/schemas/{homework,test_session}.py`, `backend/app/models/{homework,test_session}.py`, `backend/app/models/__init__.py`, `backend/app/repositories/app/homework_repo.py`, `backend/app/services/test_session_service.py` (агрегация), `backend/app/api/routers/homework.py` (новый эндпоинт), `backend/alembic/versions/005_homework_item_progress.py`, `backend/tests/test_homework_submit_test.py`
**Сопутствующий фикс (tutor):** `backend/app/services/tutor_service.py`, `backend/app/services/tutor/graph.py`, `backend/app/api/routers/tutor.py` — `Settings` инъектируется в tutor вместо глобального `get_settings()` (тест больше не ходит в реальный OpenAI).
**Scope:** M → L

---

## Task 40: Homework UI — конструктор выбора заданий (мульти-item)

> Источник: SPEC §1.7, AC-3.6. Расширяет Task 24 (форма ДЗ) под несколько пунктов из разных вариантов.

**Description:** Удобный конструктор ДЗ для преподавателя: выбор трека → добавление пунктов (лекция по теме / целый вариант / отдельные номера `type` из конкретного варианта) → список добавленных пунктов с удалением. Поддержка нескольких тестовых пунктов из **разных** вариантов в одном ДЗ.

**Acceptance criteria:**
- [ ] Можно добавить несколько items разных видов; тестовые — из разных вариантов
- [ ] Для `test_partial` — выбор конкретных номеров `type` внутри варианта
- [ ] Превью собранного ДЗ перед отправкой; удаление пункта
- [ ] Трек фиксируется по ученику; задания вне трека недоступны для выбора
- [ ] Ученик видит ДЗ как единый список пунктов с прогрессом по каждому

**Verification:**
- [ ] vitest: конструктор (добавление/удаление items, мульти-вариант)
- [ ] Ручная проверка: ДЗ из лекции + 2 заданий из разных вариантов → ученик проходит → агрегированный результат у teacher

**Dependencies:** Task 24, Task 39
**Files:** `frontend/components/homework/HomeworkForm.tsx`, `frontend/app/teacher/homework/new/page.tsx`, `frontend/lib/api/homework.ts`, `frontend/app/student/homework/[id]/page.tsx`
**Scope:** L

---

### Checkpoint: AI-советчик (после Tasks 31–38)

- [ ] Overlay-чат работает поверх учебника и тестов; ответы с цитатами
- [ ] Gating: во время теста — только теория, `correct_ans` недоступен
- [ ] Teacher видит диалоги своих учеников; RBAC проверен
- [ ] Task 38: нет устаревшего `page_context`; LLM не держит DB-транзакцию
- [ ] MVP-тесты (0–29) без регрессий

---

## Phase 10: Надёжность и расширение агента (v0.7)

> Источник: `docs/specs/tutor-rag.md` §16 (roadmap) и §17 (детальный дизайн solve-pipeline).
> **После** базового среза AI-советчика (Tasks 31–38). Каждая задача — отдельный
> вертикальный срез за фичефлагом; реальный LLM в `pytest` не вызывается (mock).
> Порядок приоритета (по §16.7): 41 → 42 → 43 → 44 → 45 → 46 → 47.

## Task 41: Анти-галлюцинации — порог retrieval + citation guard + логи (срез 16-1)

> Источник: `tutor-rag.md` §16.1 (A3, A2), §16.4 (O1). **Быстрый, высокий эффект** — без нового графа.

**Description:** Дешёвые проверки поверх текущего ReAct-графа. (A3) Retriever возвращает score; при пустом/слабом retrieval ответ — честный «не нашёл в учебнике». (A2) Узел/пост-проверка `citation_guard`: ответ по теории обязан содержать `topic`/`chunk_title` из реально вызванного `retrieve_theory`, иначе дисклеймер. (O1) `logging` INFO по tool-вызовам (имя, кол-во hits) и латентности.

**Acceptance criteria:**
- [ ] AC-16.1: при retrieval ниже порога/пустом → «не нашёл в учебнике», без выдуманных фактов
- [ ] AC-16.2: ответ по теории содержит ≥1 цитату из реально вызванного `retrieve_theory`
- [ ] Порог релевантности конфигурируем в `Settings` (напр. `rag_min_score`)
- [ ] O1: tool-вызовы и латентность логируются на INFO (без утечки `correct_ans` в логи)

**Verification:**
- [ ] `pytest backend/tests/tutor/test_guards.py` (mock): пустой retrieval → отказ; ответ без цитаты → дисклеймер
- [ ] `pytest backend/tests/tutor/test_retriever.py`: score возвращается, порог отсекает слабые hits

**Dependencies:** Task 32, Task 35
**Files:** `backend/app/services/tutor/guards.py`, `backend/app/services/tutor/graph.py`, `backend/app/services/rag/{retriever,theory}.py`, `backend/app/core/config.py`, `backend/tests/tutor/test_guards.py`
**Scope:** M

---

## Task 42: Solve-pipeline v1.5 — детерминированный разбор заданий (срез 16-2)

> Источник: `tutor-rag.md` §17 (полный дизайн). Заменяет/детализирует Task 34.
> Реализовать **в два этапа** (§17.7): A — без planner; B — с planner + LLM-критиком.

**Description:** Отдельная ветка графа для «разбери задание N» **вне** активной тест-сессии. Доступ к данным (`get_task` → `retrieve_theory`) и сверка ключа — детерминированно в коде; LLM только объясняет.

**Acceptance criteria (этап A):**
- [ ] AC-17.1: в логах виден `get_task(N)`; финальный ключ == `correct_ans` после нормализации
- [ ] AC-17.2: в разборе есть цитата (`topic`/`chunk_title`) из реально вызванного `retrieve_theory`
- [ ] `validation.py`: `digit_string` (порядок АБВГ без переупорядочивания) и `number` (допуск, `,`↔`.`, отбрасывание единиц)
- [ ] AC-17.4: во время активной `TestSession` solve-ветка не запускается (только теория)
- [ ] `intent_router` (regex задание+номер) + `prepare_context` (код) + код-критик

**Acceptance criteria (этап B):**
- [ ] AC-17.3: критик отбраковывает ключ ≠ `correct_ans` → retry; цикл ≤2; `answer_finalize` с эталоном при провале
- [ ] `planner` (`SolvePlan`) только для сложных типов 7,8,26–28; LLM-критик химической согласованности

**Verification:**
- [ ] `pytest backend/tests/tutor/test_solve.py` (mock LLM): gating, routing критика, лимит ретраев
- [ ] `pytest backend/tests/tutor/test_validation.py`: ключ/цитата/формат (вкл. соответствия, число с «хвостом»)
- [ ] AC-17.6: прежние tutor-тесты зелёные (нет регрессий общего чата)

**Dependencies:** Task 41 (citation/score переиспользуются), Task 32, Task 33, Task 14
**Files:** `backend/app/services/tutor/solve/{__init__,state,task_flow,planner,solver,critic}.py`, `backend/app/services/tutor/validation.py`, `backend/app/services/tutor/graph.py`, `backend/app/schemas/tutor.py`, `backend/tests/tutor/{test_solve,test_validation}.py`
**Scope:** L

---

## Task 43: Персональный тьютор — student tools (срез 16-3)

> Источник: `tutor-rag.md` §16.2 (student tools). Подключение агента к прикладным данным.

**Description:** Новые tools, читающие данные текущего ученика (RBAC по `user_id`): `get_my_homework()` (→ `HomeworkService`), `analyze_my_mistakes(limit)` (агрегация неверных `TestSession.steps` по `type`), `recommend_topics()` (слабые темы → учебник через маппинг `type`→`topic`).

**Acceptance criteria:**
- [ ] AC-16.4: tools возвращают данные **только** текущего ученика; `correct_ans` не утекает во время активного теста
- [ ] `analyze_my_mistakes` агрегирует по `type`/теме из реальных `TestSession`
- [ ] `recommend_topics` отдаёт темы трека ученика; маппинг `type→topic` зафиксирован (open question §16 №1)
- [ ] Tools зарегистрированы только для роли student; teacher их не видит

**Verification:**
- [ ] `pytest backend/tests/tutor/test_tools.py` (mock DB): RBAC, агрегация ошибок, gating на тесте

**Dependencies:** Task 32, Task 15 (TestSession), Task 21 (Homework)
**Files:** `backend/app/services/tutor/tools.py`, `backend/app/services/tutor/context.py`, `backend/tests/tutor/test_tools.py`
**Scope:** M

---

## Task 44: Тренажёр + suggested prompts (срез 16-4)

> Источник: `tutor-rag.md` §16.2 (`generate_practice`, `get_selfcheck`), §16.3 (U3, U4).

**Description:** Tool `generate_practice(topic/type, n)` — подбор похожих заданий для тренировки (id + текст, **без** `correct_ans` в выдаче) поверх `search_tasks`. Tool `get_selfcheck(topic)` — вопросы самопроверки из `qa_questions/qa_answers` (источник `lecture_qa`). Frontend: suggested prompts по `page_context` (U3) и кнопка «спросить советчика» из шага теста/разбора (U4).

**Acceptance criteria:**
- [ ] `generate_practice` отдаёт задания трека ученика без ключей; учёт уже решённых — по решению open question §16 №2
- [ ] `get_selfcheck` возвращает Q/A из учебника по теме
- [ ] U3: на странице темы/теста показываются контекстные подсказки-промпты
- [ ] U4: из шага теста можно открыть overlay с проброшенным `page_context`

**Verification:**
- [ ] `pytest backend/tests/tutor/test_tools.py`: practice без `correct_ans`, selfcheck по теме
- [ ] `vitest`: suggested prompts рендерятся по `page_context`; кнопка из StepView открывает чат

**Dependencies:** Task 43, Task 36 (overlay), Task 18 (StepView)
**Files:** `backend/app/services/tutor/tools.py`, `frontend/components/tutor/TutorChatOverlay.tsx`, `frontend/components/tests/StepView.tsx`, `backend/tests/tutor/test_tools.py`
**Scope:** M

---

## Task 45: Teacher-аналитика — tools (срез 16-5)

> Источник: `tutor-rag.md` §16.2 (teacher tools). Агент готовит черновики, write подтверждает преподаватель.

**Description:** Tools для преподавателя (RBAC: только свои ученики): `summarize_student(student_id)` (слабые темы, типичные ошибки, активность), `suggest_homework(student_id)` (черновик `HomeworkCreate` items под слабые темы — **без** автосоздания), `class_overview()` (агрегат ошибок по `type` всех учеников).

**Acceptance criteria:**
- [ ] RBAC: teacher получает данные только своих учеников (по `teacher_id`) → иначе пусто/403
- [ ] `suggest_homework` возвращает **черновик** (preview), создание ДЗ — обычным endpoint после подтверждения (Boundaries §16.5)
- [ ] `class_overview` агрегирует по `type` без утечки персональных ответов в общий вывод

**Verification:**
- [ ] `pytest backend/tests/tutor/test_tools.py`: RBAC teacher↔students, черновик не пишет в БД

**Dependencies:** Task 43, Task 33 (TutorSession), Task 21 (Homework)
**Files:** `backend/app/services/tutor/tools.py`, `backend/app/services/tutor/prompts.py`, `backend/tests/tutor/test_tools.py`
**Scope:** M

---

## Task 46: Hybrid retrieval 2b + eval-набор (срез 16-6)

> Источник: `tutor-rag.md` §16.1 (A4), §16.4 (O2), §4 (срез 2b). `vectorstore.py` уже есть как заготовка.

**Description:** Гибридный retrieval: keyword ∪ embeddings, rerank top-10 → top-4. Хранилище — pgvector или Chroma (ADR при старте). Eval-набор `tests/tutor/eval/`: 10–20 вопросов с эталонными `topic`/`chunk_idx`, метрика recall@5.

**Acceptance criteria:**
- [ ] `Retriever.search()` сигнатура не меняется; гибрид за фичефлагом/настройкой
- [ ] AC-16.5: eval recall@5 ≥ 0.8 на эталонном наборе, прогон в `pytest` **без** реального LLM (только retrieval/embeddings mock или локальная модель)
- [ ] ADR: pgvector vs Chroma зафиксирован

**Verification:**
- [ ] `pytest backend/tests/tutor/test_retriever.py` + `tests/tutor/eval/`: recall@5 ≥ 0.8
- [ ] Сравнение recall keyword-only vs hybrid задокументировано

**Dependencies:** Task 31 (RAG), Task 37 (deps/eval каркас)
**Files:** `backend/app/services/rag/{retriever,vectorstore,embeddings}.py`, `backend/tests/tutor/eval/*`, `docs/decisions/ADR-*-rag-store.md`
**Scope:** L

---

## Task 47: UX (streaming + markdown) + профиль в PostgreSQL (срез 16-7)

> Источник: `tutor-rag.md` §16.1 (A7), §16.3 (U1, U2), §15 (отложенный S2).

**Description:** (U1) Streaming ответов через SSE — токены по мере генерации. (U2) Markdown-рендер в `MessageBubble` + sanitization (закрывает отложенный S2). (A7) Перенос профиля ученика из JSON-файлов `tutor_profiles/` в PostgreSQL (`save_user_info` пишет в app DB по `user_id`).

**Acceptance criteria:**
- [ ] U1: ответ агента стримится в overlay; при solve-pipeline стримится финальный `solver` (open question §16 №3)
- [ ] U2: markdown (формулы, списки, таблицы) рендерится безопасно (sanitization) в `MessageBubble`
- [ ] A7: профиль в PostgreSQL, переживает рестарт/несколько воркеров; JSON-файлы больше не используются
- [ ] Alembic-миграция таблицы профиля; данные изолированы по `user_id`

**Verification:**
- [ ] `pytest backend/tests/tutor/test_memory.py`: профиль читается/пишется из PG
- [ ] `vitest`: markdown render + sanitization в `MessageBubble`; ручная проверка streaming в браузере
- [ ] `alembic upgrade head`

**Dependencies:** Task 33, Task 35, Task 36
**Files:** `backend/app/services/tutor/memory.py`, `backend/app/repositories/app/tutor_repo.py`, `backend/alembic/versions/*_tutor_profile.py`, `backend/app/api/routers/tutor.py` (SSE), `frontend/components/tutor/TutorChatOverlay.tsx`, `backend/tests/tutor/test_memory.py`
**Scope:** L

---

### Checkpoint: Надёжность агента (после Tasks 41–47)

- [ ] Анти-галлюцинации: пустой retrieval → отказ; ответ по теории всегда с цитатой (AC-16.1, 16.2)
- [ ] Solve-pipeline: ключ сверяется с `correct_ans` кодом; gating на тесте (AC-17.x)
- [ ] Персональный тьютор: ДЗ, анализ ошибок, рекомендации тем — только свои данные (AC-16.4)
- [ ] Hybrid retrieval recall@5 ≥ 0.8 на eval (AC-16.5)
- [ ] UX: streaming + markdown; профиль в PostgreSQL
- [ ] Прежние tutor-тесты (Tasks 31–38) и MVP без регрессий

---

## Phase 11: UI Redesign (SPEC §14) — визуальный язык по референсам

> Источник: `SPEC.md` §14 (design tokens, компоненты, адаптив, a11y). Референсы — `assets/` (таблица Менделеева, конспекты по химии, логотип-колба, тест-модалка); черновик-макет — `assets/textbook-redesign-teal.png`.
> **Стиль:** гибрид (чистый веб + лёгкие «бумажные» детали), **без** скевоморфизма. Главный акцент — **teal `#1d6f6b`**.
> **Scope (допущение, поправь если иначе):** кабинет **ученика** (учебник, тесты, ДЗ, дашборд, login). Кабинет преподавателя — **вне этого среза** (отдельная задача позже).
> **Адаптивность под мобилку — обязательна** (SPEC §14.5). Каждая задача — вертикальный срез, оставляет UI рабочим; `vitest` зелёный, нет console errors.

## Task 48: Design tokens + базовая тема + логотип + decorative blobs

**Description:** Завести палитру SPEC §14.1 в `frontend/app/globals.css` (teal как главный бренд, кремовый фон, blob-токены), обновить базовые `.chem-*` утилиты (primary-кнопка teal, focus-visible, section pill, callout, formula chip). Компонент `DecorativeBlobs` (SVG, `aria-hidden`). Логотип-колба (SVG из `assets/...f4cfd5c0...png`) как компонент `BrandLogo`. **Только токены/примитивы — без переверстки страниц** (срез изоляции риска).

**Acceptance criteria:**
- [ ] Токены §14.1 в `:root` + `@theme inline`; `--chem-teal` доступен как `text-chem-teal`/`bg-chem-teal`
- [ ] `.chem-btn-primary` → teal; `.chem-nav-active` → teal-индикатор; `.chem-formula`, `.chem-callout-*`, `.chem-section-pill` добавлены
- [ ] `:focus-visible` кольцо `--chem-teal` на интерактивных элементах
- [ ] `BrandLogo` и `DecorativeBlobs` рендерятся; blobs `aria-hidden`, не под текстом
- [ ] Контраст белого на `--chem-teal` ≥ 4.5:1 (проверено)

**Verification:**
- [ ] `npm run build` зелёный; `npm run test` без регрессий
- [ ] Ручная проверка: существующие экраны не сломаны (токены обратносовместимы)

**Dependencies:** —
**Files:** `frontend/app/globals.css`, `frontend/components/ui/BrandLogo.tsx`, `frontend/components/ui/DecorativeBlobs.tsx`
**Scope:** S

---

## Task 49: Редизайн страницы учебника + mobile nav

**Description:** Применить визуальный язык к учебнику (SPEC §14.2/14.3/14.5). Карточка контента (`max-w-[70ch]`), teal card-header strip с бейджем чанка, section pill, callout-боксы (маппинг эмодзи 📌/💡 → `Важно`/`Пример`, SPEC §14.4), formula chips, активный пункт сайдбара с teal-индикатором. **Мобилка:** сайдбар чанков → сворачиваемая панель сверху; контент одной колонкой; sticky низ «Назад/Далее».

**Acceptance criteria:**
- [ ] Контент в карточке, ширина текста ограничена, типографика §14.3 (line-height ~1.75)
- [ ] Section pill + callout-боксы (`Пример`/`Важно`) рендерятся; formula chips для формул
- [ ] Сайдбар: активный пункт — teal-индикатор (полоска), focus-visible
- [ ] **Mobile:** collapsible панель чанков сверху; одна колонка; sticky «Назад/Далее»; проверено на 360–414px
- [ ] Маппинг эмодзи→callout вынесен в утилиту с sanitization (XSS-safe), решение по §14.4 зафиксировано в коде

**Verification:**
- [ ] `vitest`: рендер callout/chip из markdown; collapsible nav (open/close)
- [ ] Ручная проверка в браузере (desktop + DevTools mobile 375px): нет горизонтального скролла, читаемо

**Dependencies:** Task 48
**Files:** `frontend/components/textbook/ChunkViewer.tsx`, `frontend/app/student/textbook/[topic]/page.tsx`, `frontend/components/textbook/{ChunkNav,Callout,Formula}.tsx`, `frontend/lib/textbook/markdown.ts`, `frontend/components/textbook/ChunkViewer.test.tsx`
**Scope:** M

---

## Task 50: Кастомный аудиоплеер

**Description:** Заменить нативный `<audio controls>` на кастомный pill-плеер (SPEC §14.2): круглая teal play/pause-кнопка, teal-прогресс (seek), тайминг, регулировка громкости. Доступность — клавиатура + ARIA. Источник — существующий audio-stream endpoint.

**Acceptance criteria:**
- [ ] Play/pause, seek по прогресс-бару, отображение `current / duration`
- [ ] Клавиатура: Space/Enter play-pause, стрелки seek; `aria-label`, состояние объявляется
- [ ] Стиль teal; работает с текущим `AudioPlayer`-источником (ogg stream)
- [ ] Loading/ошибка обрабатываются (нет «битого» плеера)

**Verification:**
- [ ] `vitest`: play/pause toggle, формат времени, ARIA
- [ ] Ручная проверка: воспроизведение чанка с аудио в браузере + с клавиатуры

**Dependencies:** Task 48
**Files:** `frontend/components/textbook/AudioPlayer.tsx`, `frontend/components/textbook/AudioPlayer.test.tsx`
**Scope:** M

---

## Task 51: Редизайн тестов (Stepik) + test-modal + итог

**Description:** Применить стиль к пошаговым тестам (SPEC §14.2/14.5): card-header strip, прогресс (pill «N%»/«Шаг N из M»), formula chips в вопросах, кнопки «Проверить/Подсказка/Разбор» в новом стиле, decorative blobs на экране итога. Адаптив: крупные тач-таргеты, sticky-кнопки на мобилке.

**Acceptance criteria:**
- [ ] StepView и SessionSummary в новом стиле; прогресс читаемо; verdict (верно/неверно) с цветовым кодированием
- [ ] Formula chips в тексте задания; изображения inline без переполнения на мобилке
- [ ] **Mobile:** одно задание на экран, sticky-кнопки, ≥44px тач-таргеты (360–414px)
- [ ] Decorative blobs на итоговом экране (`aria-hidden`)

**Verification:**
- [ ] `vitest`: StepView/ProgressBar/SessionSummary рендер и интеракции (без регрессий)
- [ ] Ручная проверка прохождения 3+ шагов на desktop и mobile

**Dependencies:** Task 48 (Task 50 опц. для chip-утилит)
**Files:** `frontend/components/tests/{StepView,ProgressBar,QuestionContent,VariantPicker,SessionSummary}.tsx`, `frontend/app/student/tests/**`, соответствующие `*.test.tsx`
**Scope:** M → L

---

## Task 52: Редизайн ДЗ / дашборд / login + mobile & a11y pass

**Description:** Привести к новому стилю оставшиеся экраны ученика: список/детали ДЗ, дашборд (`/student`), login. Decorative blobs на login/дашборде. Финальный проход по адаптивности (карточки в одну колонку, таблицы → карточный режим) и доступности (focus-visible везде, контраст, `aria-live` на статусах, AI-overlay не перекрывает кнопки и на мобилке — полноэкранный sheet).

**Acceptance criteria:**
- [ ] ДЗ-списки/детали, дашборд, login — в новом стиле; одноколоночны на мобилке
- [ ] AI-overlay: на мобилке полноэкранный sheet, не перекрывает «Далее»
- [ ] a11y: focus-visible на всех интерактивных, контраст ≥4.5:1, заголовки иерархичны
- [ ] Нет console errors; нет горизонтального скролла на 360–414px

**Verification:**
- [ ] `vitest` на затронутых компонентах зелёный
- [ ] Ручная проверка всех экранов ученика на desktop + mobile; быстрый прогон чеклиста `references/accessibility-checklist.md`

**Dependencies:** Task 48, Task 49, Task 51
**Files:** `frontend/app/student/**`, `frontend/components/homework/**`, `frontend/components/auth/LoginForm.tsx`, `frontend/components/tutor/TutorChatOverlay.tsx`
**Scope:** M

---

### Checkpoint: UI Redesign (после Tasks 48–52)

- [ ] Единая палитра (teal), логотип, decorative blobs; токены в `globals.css`
- [ ] Учебник, тесты, ДЗ, дашборд, login — в новом «учебном» стиле
- [ ] **Мобилка работает** на всех экранах ученика (360–414px), без горизонтального скролла
- [ ] a11y: контраст, focus-visible, клавиатура плеера, `aria-live`
- [ ] `vitest` зелёный; нет console errors; прежние тесты без регрессий
- [ ] Кабинет преподавателя — вынесен в отдельную задачу (вне scope Phase 11)

---

## Следующий шаг

1. **E2E** — teacher → assign HW (лекция + тест) → student submit → notification + score у teacher.
2. **Закоммитить** срез Tasks 20–27 (homework + notifications).
3. ~~**Task 39** — мульти-item submit (SPEC §1.7)~~ ✅ сделано (одна `TestSession` `variant_ref=null`, `HomeworkItemProgress`, общий `homework_mapper`, новый эндпоинт `items/{index}/complete`).
4. ~~**Task 40** — UI-конструктор выбора заданий (мульти-item форма, выбор `type` из разных вариантов; ученик видит per-item прогресс).~~ ✅ сделано.
5. **Task 29** — coverage check (`pytest-cov` по auth, homework, test_sessions, notifications). **← следующий.**
6. **Task 30** — Docker Compose + GitHub Actions.
7. После MVP → Phase 9 (Tasks 31–38, AI-советчик).
8. После базового советчика → Phase 10 (Tasks 41–47, надёжность и расширение агента). Начать с **Task 41** (анти-галлюцинации, срез 16-1) — дёшево и высокий эффект; затем **Task 42** (solve-pipeline, §17).
9. **Phase 11 (UI redesign, SPEC §14)** — можно вести параллельно с backend-задачами. Начать с **Task 48** (design tokens + логотип + blobs, изоляция риска), затем **Task 49** (учебник + mobile nav). Стиль: гибрид, главный акцент teal; адаптив под мобилку обязателен.
