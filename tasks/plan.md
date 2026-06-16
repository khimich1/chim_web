# Implementation Plan: Chemistry (chim_web) MVP

**Источник:** [SPEC.md](../SPEC.md) v0.4  
**Дата плана:** 2026-06-09  
**Статус:** черновик — ожидает одобрения

---

## Overview

Веб-приложение для репетитора по химии и учеников: учебник (лекции + аудио), тесты ЕГЭ/ОГЭ в стиле Stepik, домашние задания, уведомления преподавателю. Monorepo FastAPI + Next.js; контент — read-only SQLite; прикладные данные — PostgreSQL.

**Текущее состояние репозитория:** только `SPEC.md`, rules и skills. `backend/`, `frontend/` и контентные `.db` — **создать/подключить** в Task 0.

**Стратегия:** вертикальные срезы (schema → repo → service → router → frontend → тест) по приоритету P0 из spec §9.

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
Task 0  Monorepo scaffold
    │
Task 1  Config + health
    │
Task 2  PostgreSQL models + Alembic
    │
Task 3  Content SQLite repos
    │
    ├── Task 4–5   Auth (backend → frontend)
    │
    ├── Task 6–7   Students (teacher CRUD)
    │
    ├── Task 8–11  Textbook (API → audio → UI)
    │
    ├── Task 12    Grading service
    │
    ├── Task 13–16 Tests content API + images
    │
    ├── Task 17–20 TestSession (backend)
    │
    ├── Task 21–23 TestSession UI (Stepik)
    │
    ├── Task 24–28 Homework + notifications
    │
    └── Task 29–30 Dashboards + hardening
```

---

## Open Questions (из SPEC §12)

План **продолжается** с дефолтами ниже. Поправь до старта Task 4+, если нужно иначе.

| # | Вопрос | Дефолт для плана |
|---|--------|------------------|
| 1 | «Пункт 3 MVP» в исходном ТЗ | Игнорируем — в SPEC v0.4 нет отдельной фичи |
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

- [ ] Backend стартует, миграции применяются
- [ ] Content repos читают fixture SQLite
- [ ] Frontend build зелёный
- [ ] **Review с человеком:** пути к `.db`, seed teacher credentials

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

- [ ] Teacher login E2E: browser → dashboard redirect
- [ ] pytest + vitest зелёные

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

- [ ] Success criterion: ученик ЕГЭ видит темы и чанк с аудио
- [ ] pytest + vitest зелёные

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

- [ ] Success criteria: пошаговый тест с hint по запросу, итоговая сводка
- [ ] Track isolation проверен
- [ ] pytest + vitest зелёные
- [ ] **Review:** UX Stepik, нормализация ответов

---

### Phase 6: Homework (US-3)

---

## Task 20: Homework models + migration

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
- `backend/alembic/versions/003_homework.py`
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

**Description:** `POST /api/homework/{id}/submit` для item kind `lecture` — отметка прочитано, статус submitted.

**Acceptance criteria:**
- [ ] AC-3.3 для lecture
- [ ] Повторная сдача идемпотентна или 409 — зафиксировать в тесте

**Verification:**
- [ ] `pytest backend/tests/test_homework_submit_lecture.py`

**Dependencies:** Task 21

**Files:**
- `backend/app/services/homework_submit_service.py`
- `backend/tests/test_homework_submit_lecture.py`

**Scope:** S

---

## Task 23: Homework submit — test via TestSession

**Description:** Связь ДЗ `test_variant`/`test_partial` с `TestSession`; submit после `complete`; score в submission.

**Acceptance criteria:**
- [ ] AC-3.3, AC-3.4, AC-3.5 (частично — результат для teacher в Task 25)
- [ ] Partial: только выбранные `type` из варианта

**Verification:**
- [ ] `pytest backend/tests/test_homework_submit_test.py`

**Dependencies:** Task 16, Task 21

**Files:**
- `backend/app/services/homework_submit_service.py` (extend)
- `backend/tests/test_homework_submit_test.py`

**Scope:** M

---

## Task 24: Homework UI — teacher create + student list

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

- [ ] Все success criteria из SPEC §1 (кроме CI/Docker)
- [ ] Full flow: teacher creates student → assigns HW → student submits → notification
- [ ] pytest + vitest зелёные
- [ ] **Review с человеком перед polish**

---

### Phase 8: Dashboards & Hardening

---

## Task 28: Dashboards (student + teacher)

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

**Description:** Интеграционные тесты: 403 cross-user, track isolation, content DB read-only guard, cookie flags.

**Acceptance criteria:**
- [ ] Spec §5 testing strategy пункты 1–5 покрыты
- [ ] Нет утечки `correct_ans` / hint в catalog API

**Verification:**
- [ ] `pytest backend/tests/test_rbac.py`
- [ ] `pytest --cov=app` ≥80% на auth, homework, test_sessions, notifications

**Dependencies:** Task 27

**Files:**
- `backend/tests/test_rbac.py`, `backend/tests/test_security.py`

**Scope:** M

---

## Task 30: Docker Compose + CI (post-MVP slice)

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

- [ ] Все acceptance criteria SPEC §7 (US-1…US-5)
- [ ] `pytest` + `vitest` + `npm run build` зелёные
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
28 → 29 → 30 → [complete]
```

**Оценка:** ~30 задач, ~15–25 сессий агента при инкрементальной реализации.

---

## Следующий шаг

1. **Одобри план** (или укажи правки по open questions).
2. Скажи: *«Реализуй Task 0»* — начнём `incremental-implementation` по `AGENTS.md`.
