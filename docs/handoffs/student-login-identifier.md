# Handoff: логин ученика — PLAN → TASKS → IMPLEMENT

**Для:** отдельное окно Cursor Agent (новое)  
**Дата:** 2026-07-23  
**Статус входа:** idea-refine ✅ → spec ✅ (черновик, assumptions приняты по умолчанию если не оспорены) → **следующий шаг: PLAN + TASKS, затем IMPLEMENT**  
**Код по этой фиче ещё не писали.**

---

## Стартовый промпт (вставь в новое окно)

```
Следуй skills: planning-and-task-breakdown → incremental-implementation → test-driven-development.

Контекст: @docs/handoffs/student-login-identifier.md
Spec: @docs/specs/student-login-identifier.md
Idea: @docs/ideas/student-login-identifier.md

1) Сначала PLAN + атомарные TASKS (добавь секцию в tasks/plan.md или отдельный tasks/student-login-identifier.md).
2) Дождись моего «ок» по плану, затем реализуй срезами с тестами.
3) Не коммить без явной просьбы.
4) Не rename колонку/JSON email → login.
5) Отвечай по-русски.
```

---

## Цель (одна фраза)

Учитель создаёт ученика по **логину** (латиница, `@` ок), все входят по полю **«Логин»**; значение в `users.email` + `lower()`; API-ключ `email` не переименовывать.

---

## Источник правды

| Артефакт | Путь |
|----------|------|
| Spec (обязателен) | `docs/specs/student-login-identifier.md` |
| Idea one-pager | `docs/ideas/student-login-identifier.md` |
| Связь UX кабинета | `docs/specs/teacher-cabinet-ux.md` (revive по логину после `lower()`) |
| Parent product | `SPEC.md` §3 Auth, §4 онбординг |

---

## Зафиксированные решения

| Тема | Решение |
|------|---------|
| Направление | A: reuse `users.email`, без новой колонки |
| UI | Везде «логин», не «email» |
| Алфавит | Только латиница ASCII + `0-9._@+-`; кириллица → 422 |
| `@` | Разрешён |
| Normalize | `strip().lower()` при create/revive и authenticate |
| Длина | 3–64 (assumption) |
| Hint | «Только латиница, например ivanov» |
| Data migration | Alembic one-shot `lower(email)` |
| API JSON | Поля `email` / `student_email` **без rename** |
| Recovery | Только через преподавателя (уже есть) |
| Мин. пароль | **4** при установке (ученик + `seed_teacher`); login без ужесточения |

Полный список assumptions: spec §«Assumptions» (п. 1–11).

---

## Success criteria (из spec)

- Create `ivanov` → 201; create `masha@school.ru` → 201
- Кириллица → 422
- Login case-insensitive
- UI login + students (+ drawer/confirms): нет user-facing «Email»
- Hint в форме создания
- Alembic lower для существующих
- pytest students+auth + vitest затронутых форм зелёные
- JSON keys не переименованы

---

## Out of scope

Отдельный `username`, rename DB/API `email`→`login`, ФИО, invite/SSO, self-service recovery, `@local` суффиксы.

---

## Ключевые файлы сейчас

**Backend**
- `backend/app/schemas/students.py` — `StudentCreate.email`
- `backend/app/schemas/auth.py` — `LoginRequest.email`
- `backend/app/services/student_service.py` — create, 409 «Email already…»
- `backend/app/services/auth_service.py` — `authenticate` → `get_by_email`
- `backend/app/repositories/app/user_repo.py` — exact match по `User.email`
- `backend/tests/test_students.py`, `backend/tests/test_auth.py`

**Frontend**
- `frontend/components/students/CreateStudentForm.tsx` — `type="email"`, label Email
- `frontend/components/auth/LoginForm.tsx` — то же
- `frontend/components/students/StudentList.tsx`, `StudentCardDrawer.tsx`, `GroupsPanel.tsx`
- Homework/notifications UI с `student_email` — user-facing copy → «логин»
- `frontend/e2e/helpers/auth.ts` — `getByLabel("Email")` → «Логин»
- Тесты: `CreateStudentForm.test.tsx`, `LoginForm.test.tsx`, …

---

## Предлагаемый порядок срезов (для PLAN уточнить)

1. **Shared validate+normalize** (Pydantic) + unit/API tests create/login  
2. **Auth authenticate** `lower()` + test_auth  
3. **Alembic** data migration `lower(email)` (+ check collisions)  
4. **CreateStudentForm** UI «Логин» + hint + ошибки + vitest  
5. **LoginForm** + e2e helper labels  
6. **Grep copy pass:** списки, drawer, confirms, homework labels  
7. **Regression:** multi_teacher smoke / затронутые тесты  

Вертикальный минимум для демо: 1+2+4+5.

---

## Команды проверки

```bash
cd backend && source .venv/bin/activate
pytest tests/test_students.py tests/test_auth.py -q
pytest tests/multi_teacher/ -q
alembic upgrade head

cd frontend
npm run test -- CreateStudentForm LoginForm StudentList StudentCardDrawer
npm run lint
```

Dev уже может крутиться: `scripts/dev.sh` (:3000 / :8000).

---

## Skills / rules

- Plan: `.cursor/skills/planning-and-task-breakdown/SKILL.md`
- Build: `.cursor/skills/incremental-implementation/SKILL.md`
- Tests: `.cursor/skills/test-driven-development/SKILL.md`
- API: `.cursor/skills/api-and-interface-design/SKILL.md`
- UI: `.cursor/skills/frontend-ui-engineering/SKILL.md`
- Always-on: git workflow, incremental slices; **не коммитить без просьбы**

---

## Риски

- Case-collision после `lower()` у существующих users — миграция должна детектить
- Жёсткий max 64 может задеть редкие длинные email в seed/dev — проверить fixtures
- Неполный grep: останутся «Email» в e2e/homework/notifications
- Путаница: поле JSON `email` vs UI «Логин» — не «исправлять» rename в том же PR

---

## Чего не делать в новом окне без согласования

- Не расширять scope teacher-cabinet (группы, lightbox и т.д.)
- Не писать код до записанного plan/tasks и «ок» пользователя (если пользователь не сказал «сразу реализуй»)
- Не force-push / не amend чужих коммитов
