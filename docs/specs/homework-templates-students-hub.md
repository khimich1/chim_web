# Spec: Шаблоны ДЗ + хаб Ученики (вкладки, accordion, группы)

**Версия:** 0.1.0  
**Дата:** 2026-07-23  
**Статус:** ✅ approved (2026-07-23) — PLAN/TASKS в `tasks/homework-templates-students-hub.md`  
**Источник:** [`docs/ideas/homework-templates-students-hub.md`](../ideas/homework-templates-students-hub.md)  
**Родитель:** [`SPEC.md`](../../SPEC.md) §1.9 (homework), §4 (онбординг / доступ ученика)  
**Связано:** [`teacher-cabinet-ux.md`](teacher-cabinet-ux.md) (группы/revoke — переиспользуем модель; **не** drawer, **не** soft-template); [`teacher-header-chrome.md`](teacher-header-chrome.md) (вне scope); [`student-login-identifier.md`](student-login-identifier.md) (логин в UI)

> **UI amendment (2026-07-24):** accordion / checkbox-expand состава **superseded** by approved spec [`students-hub-side-panels.md`](students-hub-side-panels.md) ✅ (2026-07-24) — right sheets + dual-list. Шаблоны, groups API, soft-delete, reset-password, revoke — без изменений.

---

## Assumptions (проверьте до PLAN)

Если не поправите — считаем принятыми:

1. **Новая сущность `HomeworkTemplate`** (teacher_id, title, description?, items JSON) — отдельно от `HomeworkAssignment`. Assign копирует snapshot `items` (+ title) в assignment.
2. **Страница «Задания»** = только библиотека шаблонов (создать / список / редактировать / удалить). Блока «кому недавно назначено» нет.
3. **Старый UI «создал ДЗ = сразу выбрал ученика»** убираем: `/teacher/homework/new` → создание шаблона. `POST /api/homework` с `student_id` **не** используем из UI; либо deprecate, либо оставляем только для внутренних/тестовых нужд до среза cleanup (решить в PLAN). Существующие assignment **не** мигрируем в шаблоны.
4. **Назначение одному** — только из accordion ученика (этот ученик). **Назначение многим** — только через группу (fan-out). Multi-select учеников в одном диалоге **нет**.
5. **Группа:** при создании имя обязательно; default `"Группа N"` где N — минимальный свободный положительный номер среди групп этого учителя (`Группа 1`, если занято → `Группа 2`, …). Имя можно переименовать (PATCH). Ученик ∈ **0 или 1** группе.
6. **Выход из группы / удаление группы:** несданные assignment с `source_group_id` этой группы → `cancelled` (`assigned` | `in_progress`). `submitted` / `reviewed` не трогать. Individual (`source_group_id IS NULL`) не трогать.
7. **Статус `HomeworkStatus.CANCELLED`** добавляем в enum. Списки ученика исключают `cancelled`. У учителя в accordion (когда появится история) — можно показать с меткой; в MVP истории ДЗ в accordion **нет**.
8. **Трек-mismatch** (ЕГЭ-контент шаблона ↔ ученик ОГЭ и наоборот, где это определимо по items) → **жёсткий блок 422**, без confirm «всё равно».
9. **Accordion по клику на логин** (не drawer, не `/teacher/students/[id]`). MVP содержимое: назначить шаблон; soft-delete ученика; сброс пароля (temp один раз). История ДЗ / сессии / AI — **out**.
10. **Soft-delete** = `User.is_active=false`. Списки/пикеры только active. Login inactive → отказ. Revive: повторный create с тем же логином (после `lower`) при inactive → again active + новый temp password (как в teacher-cabinet-ux / login-identifier).
11. **Уведомление при сдаче:** тип `homework_submitted` уже есть + тест `test_homework_submit_creates_notification`. В этом релизе — **регрессия**: assign из шаблона → submit учеником → учитель видит уведомление. Новый тип уведомления **не** вводим.
12. **Правка шаблона** (title / description / items) разрешена; уже выданные assignment **не** меняются. **Удаление шаблона** не каскадит на assignment (`template_id` на assignment — ON DELETE SET NULL или nullable FK).
13. **Chrome / Конструктор-rename / paste / lightbox** — вне этого spec.
14. **Due date** при assign опционален (поле в диалоге назначения; иначе `null`).

→ Поправьте нумерованные пункты, иначе после approve идём в PLAN с ними.

---

## 1. Objective

### Что строим

1. **Шаблоны ДЗ** под пунктом nav «Задания»: собрать один раз, переиспользовать.
2. **Хаб Ученики** с вкладками Добавить / Ученики / Группы.
3. **Назначение** шаблона ученику (accordion) или группе (fan-out) за ~3 клика.
4. Админка ученика в accordion: удалить, сброс пароля.
5. Сохранить уведомление учителю при сдаче ДЗ.

### Зачем

Сейчас `HomeworkCreate` требует `student_id` — преподаватель пересобирает одно и то же под каждого. Нет групп и нет операционного хаба на `/teacher/students`.

### Для кого

| Роль | Эффект |
|------|--------|
| **Преподаватель** | Библиотека шаблонов; раздача одному или группе; управление учениками/группами |
| **Ученик** | Получает assignment как сейчас; несданные групповые пропадают при выходе из группы; inactive не входит |

### User stories + acceptance

| ID | Story | Acceptance |
|----|--------|------------|
| US-HT-1 | Создать шаблон без ученика | `POST` template → 201; в UI «Задания» виден в списке |
| US-HT-2 | Редактировать шаблон | PATCH title/items → 200; старые assignment без изменений |
| US-HT-3 | Удалить шаблон | DELETE → 204; выданные assignment остаются |
| US-HT-4 | Назначить шаблон одному из accordion | 3 клика: логин → Назначить → выбрать шаблон → OK; у ученика появляется ДЗ |
| US-HT-5 | Назначить шаблон группе | Fan-out N assignments с одним `source_group_id`; пустая группа → 422 |
| US-HT-6 | Вкладки Ученики | Добавить / Ученики / Группы; форма create только во «Добавить» |
| US-HT-7 | Accordion по логину | Строка read-only; клик по логину раскрывает панель |
| US-HT-8 | Soft-delete | DELETE student → нет в списке; login отказан |
| US-HT-9 | Reset password | POST → новый temp показан один раз |
| US-HT-10 | Группа default name | Create без имени → `"Группа 1"` (или следующий свободный N); rename OK |
| US-HT-11 | Revoke on leave | Remove member / delete group → несданные групповые `cancelled` |
| US-HT-12 | Трек-mismatch | Assign несовместимого шаблона → 422 |
| US-HT-13 | Уведомление | Submit после assign-from-template → `homework_submitted` у учителя |
| US-HT-14 | Новичок в группе | Не получает прошлые групповые раздачи автоматически |

---

## 2. Tech Stack

| Слой | Стек |
|------|------|
| Backend | FastAPI, SQLAlchemy 2 async, Alembic, Pydantic v2, pytest |
| Frontend | Next.js App Router, React client где нужны tabs/accordion, Vitest |
| Auth | httpOnly cookies, `credentials: 'include'` |
| DB | существующий app DB (SQLite/Postgres) |

Новых npm/pip зависимостей **не требуется**.

---

## 3. Commands

```bash
# Backend
cd backend
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest tests/test_homework_api.py tests/test_notifications.py -q
pytest tests/ -k "template or group or student" -q
pytest tests/multi_teacher/ -q
ruff check .
alembic upgrade head
alembic revision -m "homework_templates_groups_cancelled"

# Frontend
cd frontend
npm run dev
npm run test -- Homework StudentList CreateStudentForm
npm run lint
npm run build
```

---

## 4. Project Structure (затрагиваемое)

```
backend/
  app/
    models/           # HomeworkTemplate; StudentGroup(+Member);
                      # HomeworkAssignment.source_group_id, template_id?;
                      # HomeworkStatus.CANCELLED
    schemas/          # templates, groups, assign-from-template, students delete/reset
    api/routers/      # templates, groups; extend homework/students
    services/         # TemplateService, GroupService, assign+revoke hooks
    repositories/
  alembic/versions/
  tests/              # templates CRUD; assign; groups; revoke; mismatch;
                      # soft-delete; reset-password; notification regression;
                      # multi_teacher IDOR

frontend/
  app/teacher/
    homework/         # list = templates; new/edit = template form (no student)
    students/page.tsx # tabs shell
  components/
    students/         # tabs, accordion row, assign dialog, groups UI
    homework/         # HomeworkForm → template (drop student select)
  lib/api/            # templates, groups, assign, students delete/reset
```

---

## 5. Code Style

```python
# Snapshot on assign — never mutate template.items into live assignment by reference
assignment = HomeworkAssignment(
    teacher_id=teacher.id,
    student_id=student.id,
    title=template.title,
    items=list(template.items),  # deep-copy JSON structure in service
    source_group_id=group_id,    # or None for individual
    template_id=template.id,     # nullable provenance
    status=HomeworkStatus.ASSIGNED,
)
```

```tsx
// Accordion: only login cell is the control
<button
  type="button"
  className="text-left font-medium text-zinc-900 underline-offset-2 hover:underline"
  aria-expanded={open}
  onClick={() => setOpenId(open ? null : student.id)}
>
  {student.email}
</button>
```

Конвенции: Router → Service → Repository; Pydantic на границах; IDOR → 404/403 как в multi_teacher suite.

---

## 6. Domain model

### 6.1 HomeworkTemplate

```
HomeworkTemplate
  id, teacher_id
  title: str(1..200)
  description: str | null
  items: JSON  # same shape as HomeworkAssignment.items (1..10 items)
  created_at, updated_at
```

### 6.2 HomeworkAssignment (расширение)

```
+ source_group_id: UUID | null  FK student_groups ON DELETE SET NULL
+ template_id: UUID | null      FK homework_templates ON DELETE SET NULL
+ status: + cancelled
```

**Immutable после create:** `items`, `student_id`, `source_group_id`, `template_id`.  
**Mutable:** `title`, `due_at` (если PATCH уже есть — сохранить семантику).

### 6.3 StudentGroup

```
StudentGroup
  id, teacher_id, name (1..100), created_at

StudentGroupMember
  group_id, student_user_id
  UNIQUE(student_user_id)           # ≤1 группа глобально на ученика
  UNIQUE(group_id, student_user_id)
```

Default name algorithm (per teacher):

```
existing = names matching /^Группа (\d+)$/
n = 1
while f"Группа {n}" in existing: n += 1
return f"Группа {n}"
```

### 6.4 Assign flows

**Individual:** validate template ownership + student ownership + track compatibility → one assignment, `source_group_id=null`.

**Group:** validate non-empty members → for each member: same checks → N assignments, same `source_group_id`; transaction all-or-nothing. Если хотя бы один member mismatch — весь assign 422 (или skip? → **весь 422**, проще и честнее).

### 6.5 Revoke hook

```
UPDATE homework_assignments
SET status = 'cancelled'
WHERE student_id = :student
  AND source_group_id = :group_id
  AND status IN ('assigned', 'in_progress')
```

### 6.6 Track compatibility (MVP)

Правило минимальное, зафиксировать в service:

- Если среди items есть `test_variant` / `test_partial` / `test_by_type` с variant/types, привязанными к треку экзамена — сверить с `student.track`.
- `lecture` / `custom_theme` без явного трека — **не** блокировать (тема учителя может быть общей).
- Детали эвристики — PLAN; acceptance: явный ЕГЭ-variant item → ОГЭ student = 422.

---

## 7. API (контракт)

Все teacher endpoints: auth + role teacher + ownership. IDOR → 404/403.

### Templates

| Method | Path | Notes |
|--------|------|--------|
| GET | `/api/homework/templates` | Список шаблонов учителя |
| POST | `/api/homework/templates` | Create `{ title, description?, items }` |
| GET | `/api/homework/templates/{id}` | Деталь |
| PATCH | `/api/homework/templates/{id}` | title / description / items |
| DELETE | `/api/homework/templates/{id}` | 204; assignments keep snapshot |

### Assign

| Method | Path | Notes |
|--------|------|--------|
| POST | `/api/homework/templates/{id}/assign` | Body: `{ student_id, due_at? }` **или** `{ group_id, due_at? }` (ровно одно из student/group) → created assignment(s) |

Пустая группа / mismatch / чужой id → 422/404.

### Groups

| Method | Path | Notes |
|--------|------|--------|
| GET | `/api/teacher/groups` | Список + member count |
| POST | `/api/teacher/groups` | `{ name? }` — если name omit/blank → default `Группа N` |
| GET | `/api/teacher/groups/{id}` | + members |
| PATCH | `/api/teacher/groups/{id}` | `{ name }` rename |
| DELETE | `/api/teacher/groups/{id}` | revoke all members’ unsubmitted group HW, then delete |
| PUT | `/api/teacher/groups/{id}/members` | replace composition; on remove → revoke; enforce 0..1 |

### Students (расширение)

| Method | Path | Notes |
|--------|------|--------|
| DELETE | `/api/students/{id}` | soft `is_active=false` |
| POST | `/api/students/{id}/reset-password` | новый temp; показать once |

List/stats — только active (если ещё не так — поправить).

### Homework (ученик / notify)

| Method | Path | Notes |
|--------|------|--------|
| POST | `/api/homework/{id}/submit` | без изменения контракта; должен создавать `homework_submitted` |
| GET | student homework lists | exclude `cancelled` |

### Legacy

`POST /api/homework` (create with student_id): не использовать в новом FE. PLAN: удалить или пометить deprecated в том же релизе, если тесты позволяют без большого blast radius.

---

## 8. UI / UX

### 8.1 Задания (`/teacher/homework`)

- Список **только шаблонов** (title, дата, actions: edit / delete).
- CTA «Новое задание» → форма как сейчас по items (темы, типы, варианты…), **без** select ученика.
- Edit → та же форма, prefill.
- Delete → confirm.

Прогресс выданных ДЗ на этой странице **не** показываем (idea Q5-C). Проверка сданных — через существующие notification deep-links / homework detail flows (не ломать).

### 8.2 Ученики — вкладки

1. **Добавить** — только `CreateStudentForm`.
2. **Ученики** — таблица (логин, трек, онбординг, stats…); клик по логину → accordion.
3. **Группы** — список; создать (default name); переименовать; состав; «Назначить задание» → picker шаблона.

Tabs: client state и/или `?tab=add|list|groups`.

### 8.3 Accordion (вкладка Ученики)

- Назначить задание → picker шаблонов (+ optional due).
- Сбросить пароль → показать temp once + copy.
- Удалить ученика → confirm → soft-delete, закрыть accordion, обновить список.

**Не в MVP:** история ДЗ, открытые сессии, AI.

### 8.4 Copy

- Создание/публикация темы в Конструкторе **не** назначает ДЗ (без изменения, если уже так).
- Пустая группа: disable assign + понятная ошибка.

---

## 9. Testing Strategy

| Уровень | Где | Что |
|---------|-----|-----|
| Service / API | `backend/tests/` | Template CRUD; assign individual/group; empty group 422; mismatch 422; revoke; soft-delete; reset-password; default group name; delete template leaves assignments; submit→notification |
| IDOR | `tests/multi_teacher/` | Чужие templates/groups/students |
| Frontend | Vitest | Tabs; accordion open/close; template form без student; groups list smoke |
| Manual / e2e | по возможности | 3-click assign; group fan-out; notification после submit |

Coverage: новые service-пути — зелёные тесты обязательны до merge среза.

---

## 10. Boundaries

### Always

- TDD на template assign, groups membership, revoke, soft-delete.
- Snapshot items на assign; template edit ≠ live assignments.
- IDOR isolation.
- `pytest` / `vitest` зелёные для среза перед коммитом (когда коммит запрошен).
- Регрессия `homework_submitted` на path assign-from-template.

### Ask first

- Hard-delete студентов / каскад уничтожения ДЗ.
- Ученик в нескольких группах.
- Multi-select assign без группы.
- Новый тип уведомления.
- Миграция старых assignment → templates.
- Новые npm/pip зависимости.

### Never

- Авто-создание Homework при publish темы.
- Одна Homework-строка на группу без per-student fan-out.
- Dual UI «создал = сразу назначил одному» рядом с шаблонами.
- AI / история сессий в accordion этого релиза.
- Секреты в git.

---

## 11. Success Criteria

- [x] «Задания» = CRUD шаблонов без выбора ученика; удаление шаблона работает.
- [x] Assign шаблона одному из accordion → assignment у ученика.
- [x] Assign шаблона группе → N assignments + `source_group_id`; пустая группа — ошибка.
- [x] Вкладки Добавить / Ученики / Группы; accordion по логину.
- [x] Soft-delete + reset password из accordion.
- [x] Default имя группы `Группа N`; rename работает.
- [x] Remove/delete group → несданные групповые `cancelled`.
- [x] Трек-mismatch → 422.
- [x] Submit → уведомление учителю (существующий тип).
- [x] Новичок в группе не получает старые групповые ДЗ.
- [x] multi_teacher тесты на templates/groups зелёные.
- [x] FE/BE тесты среза зелёные; `npm run build` OK.

---

## 12. Out of scope

- История ДЗ / сессии / AI в accordion (следующий срез).
- «Недавно назначенные» на странице Задания.
- Chrome / Конструктор label / paste / lightbox.
- Invite-код вместо temp password.
- Hard-delete / уничтожение каскада ДЗ.
- Групповые отчёты и рейтинги.

---

## 13. Open Questions

Нет блокирующих после idea-refine + clarifications.  
Детали в PLAN: точная эвристика track-mismatch; shape `PUT .../members`; deprecate vs delete legacy `POST /api/homework`.

---

## 14. Decisions log

| Тема | Решение |
|------|---------|
| Модель | Template-first (`HomeworkTemplate`) |
| Задания UI | Только шаблоны; CRUD включая delete |
| Assign many | Только через группу |
| Имя группы | Default `Группа N`; rename OK |
| Accordion | Full: assign + soft-delete + reset password |
| История выданных | Позже в accordion (не на Заданиях) |
| Notify | N1 — регрессия `homework_submitted` |
| Трек-mismatch | Жёсткий 422 |
| Card UI | Accordion по логину, не drawer |
