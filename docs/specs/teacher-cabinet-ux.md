# Spec: UX кабинета преподавателя

**Версия:** 0.1.0  
**Дата:** 2026-07-22  
**Статус:** черновик — ждёт ревью человека (фаза SPECIFY)  
**Источник:** [`docs/ideas/teacher-cabinet-ux-redesign.md`](../ideas/teacher-cabinet-ux-redesign.md)  
**Родитель:** [`SPEC.md`](../../SPEC.md) §1.9 (конструктор), §4 (онбординг / доступ ученика)  
**Связано:** homework model (`HomeworkAssignment.student_id`), notifications API, multi-teacher isolation; идентификатор ученика/вход — [`student-login-identifier.md`](student-login-identifier.md) (UI «логин», хранение в `users.email`)

---

## Assumptions (проверьте до PLAN)

Если не поправите — считаем принятыми:

1. **Soft-delete ученика** = `User.is_active = false` (поле уже есть). Списки преподавателя и login ученика исключают неактивных.
2. **Повторный create с тем же логином** (поле API `email`, после `lower()`) при `is_active=false` → **revive**: снова `is_active=true`, новый temp password, тот же `user_id` / profile. Не создавать второго User. См. [`student-login-identifier.md`](student-login-identifier.md).
3. **Колокол** = существующий `NotificationBell` (dropdown + unread) переносится в `TeacherNav` слева от «Выйти»; данные unread — `GET /api/notifications/unread-count` (как сейчас). Вкладка «Уведомления» остаётся.
4. **Карточка ученика** = **right sheet (drawer)**, не modal и не `/teacher/students/[id]`.
5. **Статус отзыва** = `HomeworkStatus.CANCELLED` (`cancelled`). В истории учителя виден (фильтр «активные» по умолчанию скрывает; «все» показывает).
6. **Revoke при `in_progress`:** assignment → `cancelled`; связанные homework `TestSession` **не удаляем**; дальнейший доступ ученика к этому ДЗ → 409/410; сессия остаётся orphan для аудита (не COMPLETED принудительно — нет статуса abandoned).
7. **Items immutable** после create на любом assign (individual и group fan-out), не только групповом.
8. **Href конструктора** остаётся `/teacher/themes` (только label «Конструктор»); redirect `/teacher/constructor` — не обязателен.
9. **Удаление группы:** членство снимается; для каждого бывшего члена — тот же revoke-хук, что при remove-from-group (несданные с `source_group_id` этой группы → `cancelled`).
10. **Пустая группа:** assign-to-group → 422.

→ Поправьте нумерованные пункты, иначе идём в PLAN с ними.

---

## 1. Objective

### Что строим

Переработка UX кабинета преподавателя: единый chrome, ясное разделение «Конструктор ≠ назначение», операционный хаб **Ученики** (вкладки + карточка + группы), fan-out назначения ДЗ группе, улучшение работы со скринами (paste + lightbox).

### Зачем

Сейчас кабинет функционален, но разрознен: «Выйти»/уведомления дублируются, ученики — плоский экран без управления, групп нет, назначение оторвано от ученика, скрины неудобно смотреть при сборке и проверке.

### Для кого

| Роль | Эффект |
|------|--------|
| **Преподаватель** | Ведёт учеников и одну группу на ученика (или индивидуально), назначает ДЗ, видит прогресс в карточке, читает скрины |
| **Ученик** | Не видит отозванных ДЗ; soft-deleted не логинится |

### Приоритет поставки

**X (хаб)** → **Y (media)**. Внутри блока — по лёгкости: chrome → rename → paste → students/card → groups/assign → lightbox.

### User stories + acceptance (сводка)

| ID | Story | Acceptance (кратко) |
|----|--------|---------------------|
| US-TC-1 | Как преподаватель, хочу «Выйти» и колокол только в шапке | Нет дублей на page-headers; колокол + logout в `TeacherNav` |
| US-TC-2 | Хочу вкладку «Конструктор», а не «Темы» | Label в nav; publish не создаёт Homework |
| US-TC-3 | Хочу вставить скрин из буфера в редакторе | Paste image → upload → image block; text paste не ломается. Детали: [`clipboard-image-intake.md`](clipboard-image-intake.md) |
| US-TC-4 | Хочу вкладки Добавить / Ученики / Группы | Форма только во «Добавить»; таблица без клика в «профиль» |
| US-TC-5 | Хочу карточку ученика (drawer) | Прогресс, ДЗ, сессии, назначить, temp password, soft-delete |
| US-TC-6 | Хочу группы 0..1 и assign группе | CRUD; fan-out N assignments + `source_group_id` |
| US-TC-7 | При снятии с группы отозвать несданое групповое ДЗ | `cancelled`; submitted/reviewed не трогать |
| US-TC-8 | Хочу крупно видеть скрины | Lightbox + zoom в конструкторе и при проверке ДЗ |

---

## 2. Tech Stack

| Слой | Стек |
|------|------|
| Backend | FastAPI, SQLAlchemy 2 async, Alembic, Pydantic v2, pytest |
| Frontend | Next.js App Router, React client components где нужно, Vitest, Playwright e2e (auth helpers) |
| Auth | httpOnly cookies, `credentials: 'include'` |
| DB | PostgreSQL (prod) / существующий app DB setup проекта |

Новых внешних зависимостей для MVP **не требуется** (Clipboard API + существующий upload; drawer на CSS/существующих UI-паттернах).

---

## 3. Commands

```bash
# Backend
cd backend
# Windows: .venv\Scripts\activate
source .venv/bin/activate   # или эквивалент
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest
pytest tests/ -k "student or group or homework or notification" -q
ruff check .
alembic upgrade head
alembic revision --autogenerate -m "teacher_cabinet_groups_soft_delete"

# Frontend
cd frontend
npm run dev
npm run test
npm run test:e2e
npm run lint
npm run build
```

---

## 4. Project Structure (затрагиваемое)

```
backend/
  app/
    models/           # StudentGroup, membership; HomeworkAssignment.source_group_id;
                      # HomeworkStatus.CANCELLED; User.is_active usage
    schemas/          # groups, students (delete/reset), homework assign-group
    api/routers/      # groups router; students DELETE/POST reset-password;
                      # homework assign-group
    services/         # GroupService, extend StudentService, HomeworkService
    repositories/
  alembic/versions/
  tests/              # multi_teacher isolation для groups; homework revoke

frontend/
  components/layout/TeacherNav.tsx
  components/notifications/NotificationBell.tsx   # mount in nav
  components/students/    # tabs, StudentCard drawer, groups UI
  components/teacher/ContentBlocksEditor.tsx      # paste
  components/ui/          # ImageLightbox (shared)
  app/teacher/**          # page headers cleanup; students page tabs
  lib/api/                # groups.ts, students extend, homework assign-group
  e2e/helpers/auth.ts

docs/
  specs/teacher-cabinet-ux.md   # этот файл
  ideas/teacher-cabinet-ux-redesign.md
```

---

## 5. Code Style

Следовать существующим паттернам monorepo: Router → Service → Repository; Pydantic на границах; IDOR по `teacher_id`.

Пример контракта fan-out (ориентир, не финальный OpenAPI):

```python
class HomeworkAssignGroupRequest(BaseModel):
    group_id: uuid.UUID
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    due_at: datetime | None = None
    items: list[HomeworkItemCreate]  # как в HomeworkCreate


class HomeworkAssignGroupResponse(BaseModel):
    group_id: uuid.UUID
    created: list[HomeworkRead]  # N штук, у каждой source_group_id == group_id
```

```typescript
// frontend: drawer — 'use client'; focus trap + Escape; не отдельный route
export function StudentCardDrawer({
  studentId,
  open,
  onClose,
}: {
  studentId: string | null;
  open: boolean;
  onClose: () => void;
}) { /* ... */ }
```

---

## 6. Domain model

### 6.1 Student groups

```
StudentGroup
  id, teacher_id, name (1..100), created_at, updated_at?

StudentGroupMember
  group_id, student_user_id
  UNIQUE(student_user_id)           # глобально ≤1 группа на ученика
  UNIQUE(group_id, student_user_id)
  FK student → users; must belong to same teacher (enforced in service)
```

Инвариант: ученик преподавателя в **0 или 1** группе. Индивидуально = нет membership.

### 6.2 Homework

```
HomeworkAssignment
  ...existing...
  source_group_id: UUID | null  FK student_groups.id ON DELETE SET NULL
  # ON DELETE SET NULL: удалили группу — след provenance может обнулиться,
  # но revoke уже должен был пройти в service до delete group
```

`HomeworkStatus`:

| Value | Meaning |
|-------|---------|
| `assigned` | Назначено |
| `in_progress` | Ученик начал |
| `submitted` | Сдано |
| `reviewed` | Проверено |
| **`cancelled`** | Отозвано (выход из группы / ручной revoke later) |

**Mutable после create:** `title`, `due_at` (PATCH одной записи).  
**Immutable:** `items`, `student_id`, `source_group_id`.

### 6.3 Soft-delete student

- `User.is_active = false`.
- Не удалять profile/homework/sessions.
- List students / stats / group pickers: только `is_active=true`.
- Login: inactive → 401/403 как disabled account.
- Create same email + inactive → revive + new temp password (assumption 2).

### 6.4 Assign to group (модель C)

1. Validate group ownership + non-empty members.
2. For each member: create `HomeworkAssignment` clone of payload with `student_id=member`, `source_group_id=group.id`.
3. Return list of created reads.
4. Transaction: all-or-nothing.

### 6.5 Remove from group / delete group → revoke

Для каждого затронутого `(student, group_id)`:

```
UPDATE homework_assignments
SET status = 'cancelled'
WHERE student_id = :student
  AND source_group_id = :group_id
  AND status IN ('assigned', 'in_progress')
```

`submitted` / `reviewed` / уже `cancelled` — не трогать.  
Individual HW (`source_group_id IS NULL`) — не трогать.

Ученик: активные списки ДЗ **исключают** `cancelled`.  
Учитель: по умолчанию активные; опционально показать cancelled (бейдж «отозвано»).

---

## 7. API (контракт)

Все teacher endpoints: auth + role teacher + ownership. Multi-teacher: IDOR → 404/403 как в существующих suite.

### Groups

| Method | Path | Notes |
|--------|------|--------|
| GET | `/api/teacher/groups` | Список групп учителя (+ count members) |
| POST | `/api/teacher/groups` | `{ name }` |
| PATCH | `/api/teacher/groups/{id}` | `{ name }` |
| DELETE | `/api/teacher/groups/{id}` | Revoke хук для всех members, затем delete group/members |
| GET | `/api/teacher/groups/{id}` | Деталь + members |
| PUT | `/api/teacher/groups/{id}/members` | Заменить/патч состава; enforce 0..1; при remove → revoke |

Точный shape members update (replace vs add/remove) — выбрать в PLAN; поведение revoke на remove обязательно.

### Students (расширение)

| Method | Path | Notes |
|--------|------|--------|
| GET | `/api/students` / stats | Только active |
| POST | `/api/students` | Create **или revive** inactive same email |
| DELETE | `/api/students/{id}` | Soft: `is_active=false`; confirm на FE |
| POST | `/api/students/{id}/reset-password` | Новый temp password; body/response показать **один раз** |
| GET | `/api/students/{id}/card` | Агрегат для drawer: profile, stats, homework list, open sessions |

`card` можно собрать из существующих endpoints на FE в первом срезе; dedicated aggregate — предпочтительно для производительности (решить в PLAN).

### Homework

| Method | Path | Notes |
|--------|------|--------|
| POST | `/api/homework` | Как сейчас; `source_group_id=null`; items frozen after |
| POST | `/api/homework/assign-group` | Fan-out; см. §5 |
| PATCH | `/api/homework/{id}` | Только title/due_at; **403/422 на items** |
| GET | student homework lists | Exclude `cancelled` |

Ручной revoke endpoint — **не обязателен** в MVP (достаточно хука membership); можно добавить later.

### Notifications

Без изменения контракта: `list`, `unread-count`, `mark read`. FE: bell в nav.

### Uploads

Без изменения: paste вызывает тот же `uploadImage`.

---

## 8. UI / UX

### 8.1 Chrome (`TeacherNav`)

- Sticky header: Brand | nav links | **NotificationBell** | **LogoutButton**.
- Nav labels: Главная, Ученики, **Конструктор**, Задания, Уведомления.
- Удалить `LogoutButton` / page-level «Уведомления» / дубли bell с `/teacher`, students, themes, homework, notifications headers.
- E2E: `auth.ts` кликает «Выйти» в header.

### 8.2 Students page

Три подвкладки (client state или `?tab=`):

1. **Добавить** — только `CreateStudentForm`.
2. **Ученики** — таблица read-only (трек, онбординг, баллы…); кнопка/иконка «Управление» → drawer (не navigate на строке как на профиль).
3. **Группы** — список групп, create/edit name, состав (select учеников без группы или уже в этой), assign ДЗ.

### 8.3 Student card (drawer)

> **Детализация UI хаба (2026-07-24):** draft [`students-hub-side-panels.md`](students-hub-side-panels.md) — right sheet вместо accordion; история ДЗ через FE-filter `GET /api/homework`; AI = заглушка; `/card` отложен. Assign — через шаблоны (см. homework-templates hub), не `/teacher/homework/new?studentId=`.

MVP содержимое:

- Сводка прогресса (существующие stats).
- История ДЗ (включая cancelled с меткой, или toggle).
- Открытые сессии (если API уже отдаёт).
- CTA: Назначить ДЗ → существующий flow `/teacher/homework/new?studentId=` **или** embed form (PLAN).
- Сброс пароля → показать temp password once.
- Удалить → confirm → soft-delete.

**Не в MVP:** AI-диалоги.

### 8.4 Constructor vs assign

- Copy: создание/публикация темы **не** назначает ДЗ.
- Assign только из карточки / группы (и временно старый `/teacher/homework/new` — **не ломаем**, per idea 6C).

### 8.5 Media

**Paste / DnD:** детали intake (Ctrl+V, drag-and-drop, MIME, лимиты, hint, превью) — [`clipboard-image-intake.md`](clipboard-image-intake.md). Кратко: в `ContentBlocksEditor` paste/drop с `image/*` → `uploadImage` → image block; text paste не ломается.

**Lightbox:** клик по превью в конструкторе и в UI проверки ДЗ → modal/overlay, zoom in/out (или wheel/buttons). Один shared component. **Не** resize ширины блока в редакторе. US-TC-8 → [`image-lightbox-click-to-enlarge.md`](image-lightbox-click-to-enlarge.md) / [`tasks/image-lightbox-click-to-enlarge.md`](../../tasks/image-lightbox-click-to-enlarge.md).

---

## 9. Testing Strategy

| Уровень | Где | Что |
|---------|-----|-----|
| Unit / service | `backend/tests/` | Group membership 0..1; revive; soft-delete filters; fan-out count; revoke on remove; PATCH items rejected |
| API / integration | pytest + httpx AsyncClient | Authz IDOR groups/homework across teachers (`tests/multi_teacher/`) |
| Frontend unit | Vitest | TeacherNav labels+logout+bell; tabs; paste mock clipboard; lightbox open |
| E2E | Playwright | Logout from header; smoke students tabs если стабильно |

Coverage: новые сервисы групп/revoke — зелёные тесты обязательны до merge среза. Не требовать % глобально сверх практики репо.

---

## 10. Boundaries

### Always

- TDD на backend-логику групп, revoke, soft-delete, fan-out.
- IDOR: teacher видит только своих students/groups/homework.
- Валидация Pydantic на границах; items immutable после create.
- Обновлять e2e logout selector вместе с chrome.
- `pytest` / `vitest` зелёные для затронутого среза перед коммитом (когда коммит запрошен).

### Ask first

- Менять семантику `HomeworkStatus` beyond `cancelled`.
- Hard-delete студентов или каскадное уничтожение ДЗ.
- Менять модель вкладки «Задания» (создание только из учеников).
- Batch-edit due/items по `source_group_id`.
- Новые npm/pip зависимости для drawer/lightbox.
- Invite-link вместо temp password.

### Never

- Авто-создание Homework при `is_published` темы.
- Одна Homework-строка на группу без per-student assignments.
- Ученик в нескольких группах.
- AI в карточке в этом релизе.
- Секреты / `.env` в git.
- Force-push / `--no-verify` без явной просьбы.

---

## 11. Success Criteria

Спека считается реализованной (после PLAN/TASKS/IMPLEMENT), когда:

- [ ] На всех `/teacher/*` один «Выйти» и один колокол в шапке; нет дубля уведомлений у контента главной.
- [ ] В nav видно «Конструктор»; publish темы не создаёт ДЗ.
- [ ] Paste PNG/JPEG/WebP в конструкторе создаёт image-block; text paste в text-block работает.
- [ ] Три подвкладки на Учениках; форма только во «Добавить».
- [ ] Drawer: прогресс, ДЗ, назначить, reset password, soft-delete.
- [ ] Группы CRUD; ученик ∈ 0..1; assign-group создаёт N homework с `source_group_id`.
- [ ] Remove from group / delete group → несданные групповые ДЗ `cancelled`; submitted не тронуты.
- [ ] Новичок в группе не получает старые групповые ДЗ.
- [ ] `items` нельзя изменить PATCH после create.
- [ ] Lightbox + zoom в конструкторе и на проверке ДЗ.
- [ ] Inactive student не в списке; revive по email работает.
- [ ] multi-teacher тесты на groups не красные.
- [ ] e2e logout через header проходит.

---

## 12. Out of scope

- Редизайн главной (кроме chrome).
- AI-диалоги в карточке.
- Групповые отчёты / рейтинги.
- Invite-код вместо temp password.
- Hard-delete / уничтожение каскада ДЗ.
- Resize ширины image-block в редакторе.
- Batch update items/due по группе.
- Автовыдача ДЗ при вступлении в группу.
- Переработка IA вкладки «Задания».
- Студенческий UX `TestsPicker` «Темы».

---

## 13. Implementation order (для PLAN)

Не задачи PLAN — ориентир срезов:

1. Chrome + bell in nav + e2e  
2. Rename Конструктор + copy  
3. Clipboard paste + vitest  
4. Students tabs UI (без новых API)  
5. Student card read-only (aggregate/existing APIs)  
6. Assign from card (query param / link)  
7. Soft-delete + reset-password API+UI  
8. Groups CRUD + 0..1 + tests  
9. Assign-group fan-out + `source_group_id`  
10. Revoke on membership change  
11. Lightbox constructor + homework review  

---

## 14. Open Questions (только если отвергнете Assumptions)

| # | Если отвергаете assumption… | Альтернатива |
|---|------------------------------|--------------|
| A2 | Revive | 409 Conflict на email forever |
| A3 | Dropdown bell | Только badge-link на `/teacher/notifications` |
| A4 | Drawer | Center modal |
| A5 | `cancelled` | `revoked` |
| A6 | Orphan session | Force `TestSession.status=completed` on revoke |
| A9 | Delete group | Запретить delete, пока есть members / несданные HW |

---

## 15. Next step (gated)

1. **Human review** этого файла — подтвердить или поправить Assumptions 1–10.  
2. После OK → `planning-and-task-breakdown` → задачи в `tasks/plan.md` (или отдельный plan-файл).  
3. Затем `incremental-implementation` + TDD по срезам §13.  

**Не писать production-код**, пока Assumptions не подтверждены.
