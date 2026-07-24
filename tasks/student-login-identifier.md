# Implementation Plan: Логин ученика (identifier)

**Источник:** [`docs/specs/student-login-identifier.md`](../docs/specs/student-login-identifier.md) v0.1.0 · idea: [`docs/ideas/student-login-identifier.md`](../docs/ideas/student-login-identifier.md) · handoff: [`docs/handoffs/student-login-identifier.md`](../docs/handoffs/student-login-identifier.md)  
**Дата плана:** 2026-07-23  
**Статус:** ✅ IMPLEMENT done (2026-07-23) — ждёт коммита по просьбе пользователя  
**Skills:** planning-and-task-breakdown → incremental-implementation → TDD  
**Коммиты:** только по явной просьбе пользователя

### Progress

| Task | Статус |
|------|--------|
| LI-1 StudentCreate validate+normalize | ✅ |
| LI-2 LoginRequest normalize + 401 copy | ✅ |
| LI-3 Alembic `018` lower(email) | ✅ applied |
| LI-4 CreateStudentForm | ✅ |
| LI-5 LoginForm + e2e | ✅ |
| LI-6 Copy-pass | ✅ (Drawer/GroupsPanel отсутствуют — skip) |
| LI-7 Regression | ✅ pytest students+auth+multi_teacher; vitest forms |

---

## Overview

Учитель создаёт ученика по **логину** (латиница, `@` ок); все входят по полю **«Логин»**. Значение хранится в `users.email`, нормализуется `strip().lower()`, валидируется regex. JSON-ключи `email` / `student_email` **не переименовываем**. UI-копирайт везде «логин», не «email».

`MIN_PASSWORD_LENGTH = 4` уже в `security.py` / `seed_teacher` — в срезах только убедиться, что create/422 покрыты тестами, без дублирующей работы.

---

## Architecture Decisions

| Решение | Выбор | Почему |
|---------|--------|--------|
| Хранение | Reuse `users.email`, без новой колонки | Spec direction A; MVP без rename |
| API JSON | Поля `email` / `student_email` без rename | Совместимость клиентов; UI ≠ wire |
| Валидация | Pydantic на `StudentCreate`; login — normalize only | Spec §6.2–6.3; create жёстче, login не ломает legacy |
| Lookup | `get_by_email` exact match после normalize | Уже есть; после Alembic lower — case-insensitive вход |
| Shared regex | Константа `LOGIN_RE` (+ helper) в одном модуле schema/core | Один источник правды; без premature package |
| Revive / soft-delete | **Не в этом плане** | Scope teacher-cabinet-ux; здесь только normalize, чтобы revive потом сравнивал lower |
| Drawer / GroupsPanel | Нет в репо — skip | Copy-pass только по существующим файлам |

**ДОПУЩЕНИЯ (из spec, приняты):**
1. max_length 64 после strip; колонка БД 320 не трогаем  
2. charset `^[a-z0-9._@+-]{3,64}$` после lower; кириллица → 422  
3. `@` разрешён  
4. Alembic one-shot `lower(email)` + abort при case-collision  
5. Hint: «Только латиница, например ivanov»  
6. 409 detail → `"Login already registered"`; 401 → `"Invalid login or password"`  
7. Не rename email → login  

→ Поправь сейчас, иначе после «ок» реализуем с этим.

---

## Dependency graph

```
LI-1 StudentCreate validate+normalize (+ pytest create)
        │
        ├── LI-2 LoginRequest normalize + auth 401 copy (+ pytest auth)
        │         │
        │         └── LI-3 Alembic lower(email) + collision check
        │
        ├── LI-4 CreateStudentForm UI + vitest
        ├── LI-5 LoginForm UI + e2e helpers + vitest
        └── LI-6 Copy-pass (lists, homework labels) + vitest updates
                  │
                  └── LI-7 Regression checkpoint (multi_teacher + suite)
```

Вертикальный минимум для демо: **LI-1 + LI-2 + LI-4 + LI-5**.

---

## Task List

### Phase 1: Backend foundation (contract + auth)

---

## Task LI-1: StudentCreate — validate + normalize login

**Description:** На границе Pydantic для `POST /api/students`: `strip().lower()`, max 64, `LOGIN_RE`, ValueError → 422. Сообщение 409 в service: `"Login already registered"`. JSON-ключ остаётся `email`. TDD: сначала падающие pytest.

**Acceptance criteria:**
- [ ] `POST` с `"email": "Ivanov"` → 201, в ответе/БД `ivanov`
- [ ] `"masha@school.ru"` → 201
- [ ] `"маша"`, `"a b"`, `"ab"` (короткий), строка >64 → 422
- [ ] Повтор active того же логина в другом регистре → 409 `"Login already registered"`
- [ ] Поле JSON в request/response по-прежнему `email`

**Verification:**
- [ ] RED → GREEN: `pytest tests/test_students.py -q` (новые кейсы + старые зелёные)
- [ ] Пароль длины 4 ок / 3 → 422 (если ещё нет явного теста — добавить)

**Dependencies:** None

**Files likely touched:**
- `backend/app/schemas/students.py` (или shared `app/schemas/login_id.py` / константа рядом)
- `backend/app/services/student_service.py` (detail 409)
- `backend/tests/test_students.py`

**Estimated scope:** S–M (2–3 files)

---

## Task LI-2: LoginRequest normalize + auth error copy

**Description:** `LoginRequest.email`: `strip().lower()` (без жёсткого charset reject на login — чтобы не блокировать edge legacy до миграции; max можно оставить 320 или сузить до 64 — **рекомендация: max 64 после lower, как create**). Router detail 401: `"Invalid login or password"`. `authenticate` получает уже нормализованную строку. TDD в `test_auth.py`.

**Acceptance criteria:**
- [ ] Создан ученик `Ivanov` (через LI-1) → login `ivanov` / `IVANOV` → 200
- [ ] Неверные credentials → 401 с `"Invalid login or password"`
- [ ] JSON body login по-прежнему `{"email": "...", "password": "..."}`

**Verification:**
- [ ] `pytest tests/test_auth.py tests/test_students.py -q`
- [ ] При необходимости unit: `tests/services/test_auth_service_unit.py` (если есть кейсы на detail — не ломать)

**Dependencies:** LI-1 (для end-to-end case-insensitive create→login; normalize на LoginRequest можно писать параллельно с моками, но интеграционный кейс — после LI-1)

**Files likely touched:**
- `backend/app/schemas/auth.py`
- `backend/app/api/routers/auth.py`
- `backend/tests/test_auth.py`

**Estimated scope:** S

---

### Checkpoint: Backend login path

- [ ] Create `ivanov` + login case-insensitive работает через API
- [ ] Кириллица на create → 422
- [ ] JSON keys не переименованы
- [ ] `pytest tests/test_students.py tests/test_auth.py -q` зелёный

---

## Task LI-3: Alembic data migration — lower(email)

**Description:** Revision `018_normalize_user_email_lowercase` (следующий после `017`): one-shot `UPDATE users SET email = lower(email) WHERE email <> lower(email)`. Перед UPDATE — проверка коллизий (две строки, у которых `lower(email)` совпадает) → migration fail с понятным сообщением. Downgrade: no-op или document-only (данные irreversible без backup).

**Acceptance criteria:**
- [ ] `alembic upgrade head` приводит все `users.email` к lower-case
- [ ] При искусственной коллизии миграция падает, данные не портятся
- [ ] Колонка/индекс unique не переименовываются

**Verification:**
- [ ] Миграция применяется на dev DB (`alembic upgrade head`)
- [ ] Smoke: существующий teacher/student login после migrate
- [ ] Опционально: тест на helper collision-detect, если вынесен в callable (не обязательно гонять alembic из pytest)

**Dependencies:** LI-2 желателен (чтобы после migrate login lower был согласован); можно сразу после LI-1 если auth уже normalize

**Files likely touched:**
- `backend/alembic/versions/018_normalize_user_email_lowercase.py`

**Estimated scope:** S

---

### Phase 2: Frontend vertical slices

---

## Task LI-4: CreateStudentForm — «Логин» + hint

**Description:** Label «Логин», `type="text"`, `autoComplete="username"`, hint «Только латиница, например ivanov». Ошибки: 409 → «Этот логин уже занят.»; 422 → про логин (3–64) и пароль мин. 4. Payload по-прежнему `{ email, password, track }`. Vitest: labels, hint, payload без `@` (`ivanov`), маппинг ошибок.

**Acceptance criteria:**
- [ ] Нет user-facing «Email» в форме
- [ ] Нет `type="email"`
- [ ] Hint виден
- [ ] `createStudent` вызывается с `email: "ivanov"` (или введённым значением)
- [ ] `name="email"` можно сохранить для совместимости

**Verification:**
- [ ] `npm run test -- CreateStudentForm` (vitest)
- [ ] RED → GREEN по обновлённым assertions (`getByLabelText("Логин")`)

**Dependencies:** LI-1 (контракт ошибок); UI можно начать после согласования copy map

**Files likely touched:**
- `frontend/components/students/CreateStudentForm.tsx`
- `frontend/components/students/CreateStudentForm.test.tsx`

**Estimated scope:** S

---

## Task LI-5: LoginForm + e2e helpers

**Description:** Label «Логин», `type="text"`, ошибка «Неверный логин или пароль». Обновить `e2e/helpers/auth.ts`, `e2e/smoke.spec.ts` (`getByLabel("Логин")`). Vitest LoginForm.

**Acceptance criteria:**
- [ ] Нет user-facing «Email» на экране входа
- [ ] 401 → русский текст про логин
- [ ] E2E helper логинится по label «Логин»
- [ ] JSON/client API поле `email` без rename

**Verification:**
- [ ] `npm run test -- LoginForm`
- [ ] Grep e2e: нет `getByLabel("Email")` для auth

**Dependencies:** LI-2 (detail 401); UI copy независим от backend detail string, но согласовать

**Files likely touched:**
- `frontend/components/auth/LoginForm.tsx`
- `frontend/components/auth/LoginForm.test.tsx`
- `frontend/e2e/helpers/auth.ts`
- `frontend/e2e/smoke.spec.ts`

**Estimated scope:** S

---

## Task LI-6: Copy-pass — списки / homework / notifications

**Description:** Grep user-facing «Email»/«email» в student/auth/homework UI. `StudentList` — значение идентификатора без подписи «email». `HomeworkForm` / `HomeworkList` / notifications: где есть label про email ученика → «логин» / нейтральный текст. **Не** трогать JSON keys, OpenAPI `schema.d.ts` titles (не user-facing), переменные `studentEmail` в коде. `StudentCardDrawer` / `GroupsPanel` — отсутствуют → skip с пометкой.

**Acceptance criteria:**
- [ ] На экранах login + students (+ homework labels, если были «Email») нет user-facing «Email»
- [ ] Значения `student.email` / `student_email` по-прежнему отображаются как есть
- [ ] Vitest затронутых компонентов зелёные

**Verification:**
- [ ] `rg -n 'Email|email' frontend/components/students frontend/components/auth` — только JSON/vars/tests data, не labels
- [ ] `npm run test -- StudentList HomeworkForm HomeworkList` (затронутые)
- [ ] `npm run lint` на изменённых файлах

**Dependencies:** LI-4, LI-5

**Files likely touched:**
- `frontend/components/students/StudentList.tsx` (+ test при необходимости)
- `frontend/components/homework/HomeworkForm.tsx` / `HomeworkList.tsx` (только copy)
- `frontend/components/notifications/*` — только если есть user-facing «Email»

**Estimated scope:** S–M

---

### Checkpoint: UI demo path

- [ ] Учитель создаёт `ivanov` в UI, видит в списке
- [ ] Вход по «Логин» case-insensitive
- [ ] vitest CreateStudentForm + LoginForm зелёные

---

## Task LI-7: Regression — multi_teacher + suite smoke

**Description:** Прогнать isolation suite и убедиться, что ужесточение charset/max 64 не ломает fixtures (все ASCII email). Поправить только то, что реально падает из-за LI-*. Не чинить соседний долг.

**Acceptance criteria:**
- [ ] `pytest tests/multi_teacher/ -q` зелёный
- [ ] `pytest tests/test_students.py tests/test_auth.py -q` зелёный
- [ ] Затронутые vitest зелёные
- [ ] Success criteria spec §11 закрыты чеклистом

**Verification:**
- [ ] Команды выше
- [ ] Ручной smoke на `:3000` / `:8000` (create + login), если dev.sh уже крутится

**Dependencies:** LI-1…LI-6

**Files likely touched:**
- Только при падении fixtures: `backend/tests/**`, возможно seed emails

**Estimated scope:** S

---

### Checkpoint: Complete

- [ ] Все AC из spec §11
- [ ] Нет rename колонки/JSON `email` → `login`
- [ ] План готов к code-review; коммит — по просьбе пользователя

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Case-collision после `lower()` | High | LI-3: pre-check + abort migration |
| Fixtures с длиной >64 или unicode | Med | LI-7: поправить только сломанные; grep seeds |
| Неполный copy-pass («Email» в e2e/homework) | Med | LI-6 + explicit grep verification |
| Путаница wire `email` vs UI «Логин» | Low | Не «чинить» rename; description в OpenAPI опционально позже |
| Revive ещё нет | Low | Не scope; normalize на create готовит почву |

---

## Out of scope (явно)

- Rename DB/API `email` → `login`
- Отдельная колонка `username` / ФИО / invite / SSO
- Soft-delete + revive + StudentCardDrawer (teacher-cabinet-ux)
- Self-service recovery
- Регенерация `frontend/lib/api/schema.d.ts` как обязательный шаг (опционально после backend — description-only)

---

## Open Questions

*(нет — assumptions из spec приняты по умолчанию)*

Одно уточнение в плане (не блокирует «ок»):

- **LoginRequest max_length:** 64 (как create) vs оставить 320? **План: 64** после `strip().lower()`, чтобы вход и create совпадали.

---

## Порядок реализации после «ок»

1. LI-1 (TDD students)  
2. LI-2 (TDD auth) → Checkpoint backend  
3. LI-3 (Alembic)  
4. LI-4 → LI-5 → Checkpoint UI  
5. LI-6 → LI-7 → Checkpoint complete  

Коммиты между срезами — **только если попросишь**.

---

## Команды проверки (сводка)

```bash
cd backend && source .venv/bin/activate
pytest tests/test_students.py tests/test_auth.py -q
pytest tests/multi_teacher/ -q
alembic upgrade head

cd frontend
npm run test -- CreateStudentForm LoginForm StudentList
npm run lint
```
