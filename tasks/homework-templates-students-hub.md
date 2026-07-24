# Implementation Plan: Шаблоны ДЗ + хаб Ученики

**Источник:** [`docs/specs/homework-templates-students-hub.md`](../docs/specs/homework-templates-students-hub.md) v0.1.0 · idea: [`docs/ideas/homework-templates-students-hub.md`](../docs/ideas/homework-templates-students-hub.md)  
**Дата плана:** 2026-07-23  
**Статус:** ✅ IMPLEMENT complete — HT-1…HT-10  
**Skills:** planning-and-task-breakdown → incremental-implementation → TDD  
**Коммиты:** только по явной просьбе пользователя

### Progress

| Task | Статус |
|------|--------|
| HT-1 Migration + models | ✅ |
| HT-2 Template CRUD API | ✅ |
| HT-3 Assign → student + notify regression | ✅ |
| HT-4 FE Задания = шаблоны | ✅ |
| HT-5 Soft-delete + reset-password API | ✅ |
| HT-6 Groups CRUD + default name + revoke | ✅ |
| HT-7 Assign → group fan-out | ✅ |
| HT-8 Students tabs + accordion | ✅ |
| HT-9 Groups UI + assign | ✅ |
| HT-10 Cancelled lists + multi_teacher + checkpoint | ✅ |

---

## Overview

Преподаватель собирает **шаблон** в «Заданиях» (без ученика), затем назначает его **одному** (accordion) или **группе** (fan-out). Хаб Ученики: вкладки Добавить / Ученики / Группы. Soft-delete + сброс пароля в accordion. Уведомление `homework_submitted` — регрессия, без нового типа.

---

## Architecture Decisions

| Решение | Выбор | Почему |
|---------|--------|--------|
| Template storage | Таблица `homework_templates` | Spec; не путать со статусами assignment |
| Snapshot | Deep-copy `items` в `HomeworkAssignment` при assign | Правка шаблона ≠ выданные |
| Provenance | `template_id` nullable ON DELETE SET NULL; `source_group_id` nullable ON DELETE SET NULL | Удаление шаблона/группы не ломает историю |
| Cancelled | `HomeworkStatus.CANCELLED` | Spec revoke X |
| Legacy `POST /api/homework` | Оставить endpoint в релизе; FE не использует; тесты, что создают assignment напрямую, постепенно переводим на template→assign или оставляем как low-level create | Меньше blast radius; cleanup later |
| Teacher GET `/api/homework` | Оставить (detail/review/notify links) | Страница list UI = templates only |
| Members update | `PUT .../members` = **replace** полный список id | Проще revoke-on-diff |
| Track mismatch MVP | Если item `test_variant` / `test_partial` / `test_by_type` резолвится в track ≠ `student.track` → 422; `lecture` / `custom_theme` не блокируют | Spec §6.6; эвристика в service helper |
| Group assign mismatch | Любой member mismatch → **весь** assign 422 (транзакция) | Spec |
| Default group name | `Группа {n}` минимальный свободный n у teacher | Spec |
| Accordion | Client state в `StudentList` / wrapper; один open id | Нет drawer |
| Tabs | `?tab=add\|list\|groups` + client | Deep-link ок |
| Revive | В soft-delete срезе: create same login + inactive → revive + new temp | Spec assumption 10 |

**Риски**

| Риск | Митигация |
|------|-----------|
| Route order `/api/homework/templates` vs `/{id}` | Регистрировать templates **до** `/{assignment_id}` или отдельный router prefix |
| SQLite enum `cancelled` | `native_enum=False` уже; добавить значение в Python enum + data ok |
| Track heuristic ложные 422 | Узкое правило + тесты; custom_theme не трогать |
| Большой FE diff | Срезы HT-4 → HT-8 → HT-9 по отдельности |

---

## Dependency graph

```
HT-1 models + Alembic 019
 │
 ├── HT-2 Template CRUD API (+ pytest)
 │     │
 │     ├── HT-3 Assign→student + mismatch + notify regression
 │     │     │
 │     │     └── HT-4 FE Задания = templates (list/new/edit/delete)
 │     │
 │     └── HT-7 Assign→group (needs HT-6)
 │
 ├── HT-5 Soft-delete + reset-password (+ revive)
 │
 └── HT-6 Groups CRUD + members + revoke + default name
           │
           └── HT-7 Assign→group fan-out
                     │
                     ├── HT-8 Students tabs + accordion (needs HT-3, HT-5)
                     ├── HT-9 Groups UI (needs HT-6, HT-7)
                     └── HT-10 cancelled filter + multi_teacher + checkpoint
```

**Демо-минимум (3 клика):** HT-1 → HT-2 → HT-3 → HT-4 (+ простой picker на homework page временно **не** делаем — сразу accordion в HT-8).  
Практичный early path: после HT-4 учитель уже создаёт шаблоны; assign из UI — с HT-8.

---

## Task List

### Phase 1: Foundation

---

## Task HT-1: Migration + ORM models

**Description:** Alembic `019`: таблицы `homework_templates`, `student_groups`, `student_group_members`; колонки `homework_assignments.source_group_id`, `template_id`; значение статуса `cancelled` (Python enum). Models + exports в `app.models`.

**Acceptance criteria:**
- [x] `alembic upgrade head` / downgrade проходит на чистой и существующей dev DB
- [x] ORM: `HomeworkTemplate`, `StudentGroup`, `StudentGroupMember`; FKs как в spec
- [x] `HomeworkStatus.CANCELLED == "cancelled"`

**Verification:**
- [x] `alembic upgrade head`
- [x] `pytest tests/test_models.py -q` (добавить smoke create template/group если уместно)

**Dependencies:** None

**Files likely touched:**
- `backend/alembic/versions/019_*.py`
- `backend/app/models/homework.py` (или `templates.py` / `groups.py`)
- `backend/app/models/enums.py`
- `backend/app/models/__init__.py`

**Estimated scope:** M

---

## Task HT-2: Template CRUD API

**Description:** Schemas + repository + service + router `GET/POST/PATCH/DELETE /api/homework/templates[/{id}]`. Items = тот же discriminated union, что у homework. TDD.

**Acceptance criteria:**
- [x] Teacher CRUD только своих шаблонов
- [x] IDOR → 404/403
- [x] items 1..10; validation как HomeworkCreate без student_id
- [x] DELETE → 204; не удаляет assignments (пока assignments ещё без template_id в create — ok)

**Verification:**
- [x] `pytest tests/test_homework_templates.py -q` (новый файл)

**Dependencies:** HT-1

**Files likely touched:**
- `backend/app/schemas/homework_templates.py`
- `backend/app/services/homework_template_service.py`
- `backend/app/repositories/app/homework_template_repo.py`
- `backend/app/api/routers/homework_templates.py` (+ `main.py` include)
- `backend/tests/test_homework_templates.py`

**Estimated scope:** M

---

### Checkpoint: Templates API

- [x] Create/list/patch/delete template через API
- [x] `pytest tests/test_homework_templates.py -q` green

---

### Phase 2: Assign individual + FE library

---

## Task HT-3: Assign template → student + notify regression

**Description:** `POST /api/homework/templates/{id}/assign` с `{ student_id, due_at? }`. Snapshot items; `template_id` set; `source_group_id=null`. Track mismatch → 422. После assign студент submit → `homework_submitted` (существующий путь). Exclude `cancelled` в student list если ещё не сделано (можно заготовка). TDD.

**Acceptance criteria:**
- [x] Assign → 201, assignment у студента с копией items
- [x] PATCH template items ≠ изменение уже созданного assignment
- [x] ЕГЭ-variant item → ОГЭ student → 422
- [x] Submit → notification type `homework_submitted` у teacher

**Verification:**
- [x] `pytest tests/test_homework_templates.py tests/test_notifications.py -q` (новые кейсы assign)

**Dependencies:** HT-2

**Files likely touched:**
- `backend/app/schemas/homework_templates.py` (AssignBody)
- `backend/app/services/homework_template_service.py` / `homework_service.py`
- `backend/app/services/track_compat.py` (или helper рядом)
- `backend/tests/test_homework_templates.py`

**Estimated scope:** M

---

## Task HT-4: FE «Задания» = шаблоны

**Description:** Страницы homework list/new/(edit): без student select; API client templates. Удаление с confirm. Список assignment на `/teacher/homework` заменяем на templates.

**Acceptance criteria:**
- [x] Создать шаблон из UI без выбора ученика
- [x] Список / edit / delete шаблона
- [x] Vitest: форма без student field; list templates

**Verification:**
- [x] `npm run test -- Homework` (+ TemplateList)
- [ ] Manual: `/teacher/homework` CRUD шаблона

**Dependencies:** HT-2 (HT-3 желателен, но FE library может идти после HT-2)

**Files likely touched:**
- `frontend/lib/api/homework.ts` / `templates.ts`
- `frontend/components/homework/HomeworkForm.tsx` (+ tests)
- `frontend/app/teacher/homework/**`

**Estimated scope:** L

---

### Checkpoint: Library usable

- [x] Teacher создаёт и удаляет шаблон в UI
- [x] Assign API работает (хотя UI assign ещё нет)

---

### Phase 3: Students admin + groups backend

---

## Task HT-5: Soft-delete + reset-password (+ revive)

**Description:** `DELETE /api/students/{id}` → `is_active=false`. `POST .../reset-password` → новый temp в response. List/stats фильтр active. Create same login + inactive → revive. TDD.

**Acceptance criteria:**
- [x] Soft-delete: нет в list; login отказан
- [x] Reset: 200 + temp password once
- [x] Revive: create same login → active + новый password, same user id

**Verification:**
- [x] `pytest tests/test_students.py -q`

**Dependencies:** None (параллельно с HT-2..4 после HT-1 не обязательно; можно после HT-1)

**Files likely touched:**
- `backend/app/services/student_service.py`
- `backend/app/api/routers/students.py`
- `backend/app/repositories/app/student_repo.py`
- `backend/tests/test_students.py`

**Estimated scope:** M

---

## Task HT-6: Groups CRUD + members + revoke + default name

**Description:** Router `/api/teacher/groups`. Create с default `Группа N`. PATCH rename. PUT members replace + revoke on remove. DELETE group → revoke all then delete. UNIQUE student ≤1 group. TDD.

**Acceptance criteria:**
- [x] Default names `Группа 1`, `Группа 2`, …
- [x] Student не может быть в двух группах
- [x] Remove member → несданные group HW `cancelled`
- [x] Empty group allowed; assign later 422 (HT-7)

**Verification:**
- [x] `pytest tests/test_teacher_groups.py -q`

**Dependencies:** HT-1 (revoke нужен cancelled + source_group_id; assign group в HT-7 создаст HW с group id — revoke тесты можно с factory assignment)

**Files likely touched:**
- `backend/app/schemas/groups.py`
- `backend/app/services/group_service.py`
- `backend/app/api/routers/teacher_groups.py`
- `backend/tests/test_teacher_groups.py`

**Estimated scope:** L

---

## Task HT-7: Assign template → group

**Description:** Тот же assign endpoint с `{ group_id, due_at? }`. Fan-out N; all-or-nothing; empty → 422; mismatch any → 422. `source_group_id` set.

**Acceptance criteria:**
- [x] 3 members → 3 assignments, same `source_group_id` + `template_id`
- [x] Empty group → 422
- [x] Один ОГЭ в ЕГЭ-группе-раздаче → весь 422, 0 созданных

**Verification:**
- [x] `pytest tests/test_homework_templates.py -k group -q`
- [x] Revoke integration: assign → remove member → cancelled

**Dependencies:** HT-3, HT-6

**Files likely touched:**
- `backend/app/services/homework_template_service.py`
- `backend/tests/test_homework_templates.py`
- `backend/tests/test_teacher_groups.py`

**Estimated scope:** M

---

### Checkpoint: Backend complete

- [x] Templates + assign individual/group + groups + soft-delete/reset green in pytest
- [x] Notification regression green

---

### Phase 4: Students hub UI

---

## Task HT-8: Students tabs + accordion

**Description:** `/teacher/students`: tabs Добавить / Ученики / Группы (Groups tab shell ok). List tab: accordion по логину — назначить (picker templates), reset password, delete. Wire HT-3/HT-5 APIs.

**Acceptance criteria:**
- [x] Форма create только на «Добавить»
- [x] Клик по логину раскрывает панель; повторный клик закрывает
- [x] Assign шаблона → успех; reset показывает temp; delete убирает из списка

**Verification:**
- [x] `npm run test -- StudentList CreateStudentForm`
- [ ] Manual: 3-click assign одному

**Dependencies:** HT-3, HT-4 (templates list for picker), HT-5

**Files likely touched:**
- `frontend/app/teacher/students/page.tsx`
- `frontend/components/students/*`
- `frontend/lib/api/students.ts` / templates

**Estimated scope:** L

---

## Task HT-9: Groups UI + assign шаблона группе

**Description:** Вкладка Группы: create (default name), rename, members picker (ученики без группы или уже в этой), assign template.

**Acceptance criteria:**
- [x] Создать группу → видно `Группа N`
- [x] Состав save; нельзя добавить ученика из другой группы без снятия (UI + API error)
- [x] Назначить шаблон непустой группе → N ДЗ

**Verification:**
- [x] Vitest groups panel smoke
- [ ] Manual: fan-out + remove member → ДЗ отозвано у ученика

**Dependencies:** HT-6, HT-7, HT-8 (tabs shell)

**Files likely touched:**
- `frontend/components/students/GroupsPanel.tsx` (new)
- `frontend/lib/api/groups.ts`

**Estimated scope:** L

---

## Task HT-10: Cancelled visibility + multi_teacher + final checkpoint

**Description:** Student homework lists exclude `cancelled`. Teacher detail показывает cancelled если открыт по id (или 404 — выбрать: **показывать с status cancelled** учителю). multi_teacher IDOR suite для templates/groups. FE build. Fix any leftover legacy FE calling create-with-student.

**Acceptance criteria:**
- [x] Ученик не видит cancelled в списке
- [x] IDOR tests green
- [x] `npm run build` OK
- [x] Spec success criteria checklist пройден по пунктам MVP

**Verification:**
- [x] `pytest tests/multi_teacher/ tests/test_homework_templates.py tests/test_teacher_groups.py tests/test_students.py tests/test_notifications.py -q`
- [x] `cd frontend && npm run test && npm run build`

**Dependencies:** HT-7, HT-8, HT-9

**Files likely touched:**
- `backend/app/services/homework_service.py` (list filters)
- `backend/tests/multi_teacher/*`
- FE leftovers

**Estimated scope:** M

---

### Final Checkpoint

- [x] US-HT-1…14 покрыты или явно отложены (история в accordion — out)
- [x] Нет dual UI create-with-student на FE
- [x] pytest + vitest + build green

---

## Out of this plan (explicit)

- История ДЗ / сессии / AI в accordion
- Chrome / Конструктор rename / paste / lightbox
- Удаление legacy `POST /api/homework`
- Миграция старых assignment → templates

---

## Open PLAN choices (не блокируют старт HT-1)

1. Track helper: резолв variant filename → track через существующие content repos / naming — уточнить в HT-3 по коду.
2. Teacher GET list assignments: оставить API-only без UI list на `/teacher/homework`.
3. Accordion: один открытый ряд vs несколько — **один** (проще).

→ Напиши **ок** / правки по Task/AD — затем IMPLEMENT с HT-1.
