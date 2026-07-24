# Spec: Конструктор (nav) + отзыв ДЗ в хабе Ученики

**Версия:** 0.1.0  
**Дата:** 2026-07-24  
**Статус:** ✅ complete — CR-1…CR-10 implemented  
**Источник:** [`docs/ideas/constructor-nav-and-homework-revoke.md`](../ideas/constructor-nav-and-homework-revoke.md)  
**Plan:** [`tasks/constructor-nav-and-homework-revoke.md`](../../tasks/constructor-nav-and-homework-revoke.md)  
**Родитель / baseline:** [`students-hub-side-panels.md`](students-hub-side-panels.md) (sheets as-is), [`homework-templates-students-hub.md`](homework-templates-students-hub.md) (`cancelled`, fan-out, revoke-on-leave)  
**Связано:** [`teacher-header-chrome.md`](teacher-header-chrome.md) — rename «Темы»→«Конструктор» был **out**, этот spec его закрывает

---

## Assumptions (проверьте до PLAN)

Если не поправите — считаем принятыми:

1. **Один MVP:** (a) rename nav/заголовков, (b) история раздач в `GroupSidePanel`, (c) явный отзыв корзиной в student + group sheets, (d) API cancel/restore с TTL 30 с.
2. **Nav label:** коротко **«Конструктор»**; `aria-label` и `title` = **«Конструктор заданий»**. Заголовки `/teacher/themes` и кнопка на `/teacher` («Конструктор тем») → **«Конструктор заданий»** (или коротко «Конструктор» где уже коротко). URL `/teacher/themes` **не** меняем.
3. **Вкладка «Темы» у ученика** в `TestsPicker` — **не трогаем**.
4. **Group sheet — история:** тот же UX-паттерн, что у ученика (список с title, status, due; `cancelled` с меткой). Данные: `GET /api/homework` → filter `source_group_id === group.id`. **Одна строка = одна волна** раздачи, не N строк по ученикам.
5. **Ключ волны:** при group fan-out писать общий **`assign_batch_id`** (UUID) на все копии; у individual assign — `assign_batch_id = null`. Строка группы группируется по `assign_batch_id`. (Альтернатива «heuristic по created_at» — хуже при двух подряд assign одного шаблона; batch_id — Ask first только если хотите без миграции колонки.)
6. **После assign / cancel / restore** список в открытом sheet **сразу** перечитывается (тот же `listHomework` + filter).
7. **Deep-link:** строка может вести на `/teacher/homework/{id}` (для волны — любой id из батча, предпочтительно первый). Можно убрать позже без ломки API.
8. **Корзина (UI):** только иконка (с `aria-label`), без отдельной текстовой кнопки «Отозвать». Confirm-модалка **не** нужна — аккуратность = **toast «Вернуть» 30 с**.
9. **Cancel семантика (как revoke-on-leave):** только `assigned` / `in_progress` → `cancelled`. `submitted` / `reviewed` **никогда** не трогаем. Hard-DELETE строк — out.
10. **Student sheet:** корзина на **одну** строку assignment → cancel только этого id.
11. **Group sheet:** корзина на строку волны → cancel всех несданных с тем же `assign_batch_id` (и `source_group_id` этой группы). В ответе/UI: сколько отозвано, сколько пропущено как уже сданные.
12. **Undo 30 с:** cancel **сразу** ставит `cancelled` + `cancelled_at=now()`; ученик сразу не видит ДЗ. `POST …/restore` разрешён только если `now - cancelled_at ≤ 30s` и status ещё `cancelled`; возвращает в `assigned` (если был `in_progress` до cancel — **упрощаем: всегда restore → `assigned`**, progress items не восстанавливаем специально beyond existing rows). После TTL restore → **409**. Клиентский таймер только для UX toast; источник истины — сервер.
13. **Revoke-on-leave / delete group** тоже выставляют `cancelled_at` (для консистентности); restore этих отзывов **не** требуется в MVP (кнопки undo нет) — но поле пишется.
14. **Ученик при отзыве:** без уведомления «отозвали». Тип `homework_assigned` в notifications **нет** — чистить нечего. «Пропало полностью» = student `GET /api/homework` по-прежнему **исключает** `cancelled`; resume / recommended actions не показывают этот id.
15. **Teacher history:** `cancelled` остаётся видимым в sheet (метка «Отозвано» / «Отменено»); корзины на уже `cancelled` нет (или disabled).
16. **Миграция:** Alembic — колонки `homework_assignments.assign_batch_id` (UUID nullable, index) и `cancelled_at` (timestamptz nullable).
17. **Тесты:** pytest на cancel/restore/TTL/wave/partial-submitted; Vitest на корзину + toast undo + group history grouping + nav label; multi_teacher IDOR на новых endpoints.
18. **Не стартуем IMPLEMENT** до явного approve этого spec.

→ Поправьте нумерованные пункты, иначе после approve идём в PLAN с ними.

---

## 1. Objective

### Что строим

Три связанных среза в одном релизе:

1. Переименование вкладки преподавателя «Темы» → «Конструктор» (полное имя — конструктор заданий).
2. В right sheet группы — отображение истории/актуальных назначенных ДЗ (волнами).
3. Явный отзыв ДЗ корзиной у ученика и у группы + 30-секундный undo.

### Зачем

Сейчас можно назначить шаблон ученику/группе, но нельзя аккуратно снять тестовые или ошибочные раздачи иначе как побочным эффектом состава группы. В group sheet после assign пусто — нет обзора «что уже выдано». Nav «Темы» путается с ученической вкладкой и со смыслом конструктора заданий.

### Для кого

| Роль | Эффект |
|------|--------|
| **Преподаватель** | Видит раздачи группе; снимает несданные корзиной; 30 с на «Вернуть»; ясное имя раздела конструктора |
| **Ученик** | Отозванное ДЗ исчезает из списка без отдельного notify |

### User stories + acceptance

| ID | Story | Acceptance |
|----|--------|------------|
| US-CR-1 | Nav «Конструктор» | В `TeacherNav` label «Конструктор»; `aria-label`/`title` «Конструктор заданий»; ссылка `/teacher/themes` |
| US-CR-2 | Заголовки themes | `/teacher/themes` (+ home CTA) не говорят только «Темы» как nav; согласованы с «Конструктор заданий» |
| US-CR-3 | История в group sheet | Открыта группа → виден список волн (title, агрегированный status summary, due); cancelled с меткой |
| US-CR-4 | Refresh | Assign / cancel / restore → список в sheet обновляется без закрытия панели |
| US-CR-5 | Cancel у ученика | Корзина на активной строке → assignment `cancelled`; ученик не видит в своём списке |
| US-CR-6 | Cancel волны | Корзина на строке группы → все несданные копии батча `cancelled`; сданные нетронуты; UI отражает counts |
| US-CR-7 | Undo 30 с | После cancel — toast/action «Вернуть» ≤30 с → status снова `assigned`; после 30 с restore 409 |
| US-CR-8 | Нет student notify об отзыве | Нет нового notification type; нет toast ученику |
| US-CR-9 | IDOR | Учитель A не может cancel/restore ДЗ учителя B |

---

## 2. Tech Stack

| Слой | Стек |
|------|------|
| Frontend | Next.js App Router, React `'use client'`, Vitest + RTL |
| Backend | FastAPI, SQLAlchemy 2, Alembic, pytest |
| API | Расширение homework router; reuse `listHomework`, templates assign |
| UI | Существующие `chem-*` / sheet patterns; без новых npm UI-libs |

---

## 3. Commands

```bash
# Backend
cd backend
pytest tests/test_homework_cancel.py tests/test_homework_templates.py tests/test_teacher_groups.py tests/multi_teacher/ -q
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run test -- TeacherNav StudentSidePanel GroupSidePanel
npm run lint
npm run dev
```

Dev: `http://localhost:3000/teacher/students?tab=groups` + FastAPI `:8000`.

---

## 4. Project Structure

```
backend/
  alembic/versions/0xx_homework_cancel_batch.py   # assign_batch_id, cancelled_at
  app/models/homework.py                          # + fields
  app/schemas/homework.py                         # + fields on read; cancel/restore responses
  app/api/routers/homework.py                     # POST cancel, restore (+ optional wave)
  app/services/homework_service.py                # cancel / restore / wave logic
  app/repositories/app/homework_repo.py           # queries
  app/repositories/app/student_group_repo.py      # revoke paths set cancelled_at
  app/services/homework_template_service.py       # fan-out sets assign_batch_id
  tests/test_homework_cancel.py                   # NEW

frontend/
  components/layout/TeacherNav.tsx                # label + aria
  app/teacher/themes/page.tsx                     # heading copy
  app/teacher/page.tsx                            # CTA copy
  components/students/StudentSidePanel.tsx        # trash + undo toast
  components/students/GroupSidePanel.tsx          # history waves + trash + undo
  lib/api/homework.ts                             # cancelHomework, restoreHomework
  lib/students/groupHomeworkWaves.ts              # NEW: group rows by assign_batch_id (optional)
  *.test.tsx

docs/ideas/constructor-nav-and-homework-revoke.md
docs/specs/constructor-nav-and-homework-revoke.md  # this file
tasks/constructor-nav-and-homework-revoke.md       # после approve → PLAN
```

---

## 5. Code Style

### API (ориентир)

```
POST /api/homework/{assignment_id}/cancel
  Auth: teacher owner
  Body (optional): { "scope": "single" | "wave" }  # default single
  single: cancel this id if assigned|in_progress
  wave: require source_group_id + assign_batch_id; cancel all siblings
        same teacher_id + assign_batch_id in assigned|in_progress
  Response 200: {
    cancelled_ids: uuid[],
    skipped_submitted_count: int,
    cancelled_at: datetime
  }
  409 if already terminal in a way that yields zero cancels and not cancelled? 
  → Prefer 200 with cancelled_ids=[] + skipped_*; or 404/403 IDOR

POST /api/homework/{assignment_id}/restore
  Auth: teacher owner
  Restores this id if status=cancelled and cancelled_at within 30s
  For wave undo from group UI: body { "scope": "wave" } restores all
        cancelled siblings of batch with cancelled_at within 30s
        (same cancelled_at batch / same assign_batch_id cancelled in that action)
  Response 200: { restored_ids: uuid[] }
  409 if TTL exceeded or not cancelled
```

### FE (ориентир)

```tsx
<button
  type="button"
  aria-label={`Отозвать задание «${title}»`}
  onClick={() => void onCancel(row)}
  disabled={busy || !canCancel}
>
  {/* trash icon — existing icon pattern / inline SVG */}
</button>

{undo && (
  <div role="status" className="chem-callout …">
    Отозвано.
    <button type="button" onClick={() => void onRestore(undo)}>
      Вернуть
    </button>
  </div>
)}
```

- Русские строки как в кабинете.
- Не дублировать серверный TTL на FE как единственную защиту.
- Group rows: показывать summary вроде `2 уч. · 1 сдано · 1 активно` (точные формулировки — по месту, кратко).

---

## 6. Testing Strategy

| Уровень | Что |
|---------|-----|
| pytest | cancel single; cancel wave (2 members → 2 cancelled); wave skips submitted; restore within 30s; restore after 31s → 409; IDOR other teacher; fan-out пишет один `assign_batch_id`; revoke-on-leave sets `cancelled_at` |
| Vitest | Nav «Конструктор»; group sheet показывает сгруппированные волны; trash вызывает cancel API; undo вызывает restore; после cancel список refresh |
| Manual | Назначить группе → строка в истории → корзина → ДЗ пропало у ученика → Вернуть &lt;30 с → снова видно; &gt;30 с — нельзя |

Coverage: затронутые модули зелёные; глобальный % не раздувать ради этой фичи.

---

## 7. Boundaries

### Always

- Только `assigned` / `in_progress` → `cancelled` на explicit cancel и на revoke-on-leave.
- Student list скрывает `cancelled` (регрессия).
- Server-side TTL 30 с для restore.
- a11y: у корзины осмысленный `aria-label`; undo в `role="status"`.
- multi_teacher: teacher_id check на cancel/restore.

### Ask first

- Отказаться от `assign_batch_id` в пользу heuristic grouping.
- Hard-DELETE вместо `cancelled`.
- Undo длиннее/короче 30 с.
- Новый notification type ученику.
- Rename URL `/teacher/themes` → `/teacher/constructor`.
- Restore в прежний `in_progress` (не в `assigned`).

### Never

- Трогать вкладку «Темы» ученика в `TestsPicker` в этом релизе.
- Отзывать `submitted` / `reviewed` без отдельного approve.
- Confirm-модалка как замена undo (если не откатите Assumption 8).
- IMPLEMENT до approve spec.
- Смешивать с ambient-background / clipboard / другими specs.

---

## 8. Success Criteria

- [x] `TeacherNav` показывает «Конструктор» с полным accessible name «Конструктор заданий».
- [x] Group sheet: история волн после assign; immediate refresh.
- [x] Корзина в student sheet отзывает одно несданное ДЗ; ученик не видит его в списке.
- [x] Корзина в group sheet отзывает несданные копии волны; сданные остаются.
- [x] «Вернуть» ≤30 с восстанавливает; после TTL — нет.
- [x] pytest + Vitest затронутых сюитов зелёные; IDOR покрыт.
- [x] Revoke-on-leave / delete group по-прежнему отзывают несданные и пишут `cancelled_at`.

---

## 9. Out of scope

- Hard delete assignments / cascade wipe submissions.
- Per-student checkbox revoke внутри group wave.
- Отдельная сущность `GroupAssignment` (кроме поля `assign_batch_id` на существующих rows).
- Notify ученику об отзыве / новый `NotificationType`.
- Rename student «Темы» / смена path `/teacher/themes`.
- Chrome ambient, tutor AI, homework template editor redesign.

---

## 10. Open Questions

1. **Restore после `in_progress`:** всегда → `assigned` (Assumption 12) — ок, или вернуть `in_progress`?
2. **Wave undo:** restore всех id из последнего cancel response vs всех cancelled siblings batch с `cancelled_at` в окне 30 с?
3. **Иконка корзины:** есть ли уже shared trash icon в FE, или inline SVG в panel?

Неблокирующие для approve, если оставляем дефолты: (1) → `assigned`, (2) restore ids из cancel response / same batch+TTL, (3) inline SVG ok.

---

## 11. Amendment к предыдущим specs

| Spec | Было | Станет |
|------|------|--------|
| `teacher-header-chrome` | Rename «Темы»→«Конструктор» — out | **In** — этот документ |
| `students-hub-side-panels` | Group sheet: assign/rename/delete; истории раздач группе нет | + история волн + revoke UI |
| `homework-templates-students-hub` | `cancelled` только via revoke-on-leave / delete group | + explicit cancel/restore API; `assign_batch_id`, `cancelled_at` |

---

**Approve?** Spec ещё draft; PLAN уже в [`tasks/constructor-nav-and-homework-revoke.md`](../../tasks/constructor-nav-and-homework-revoke.md). Ответь «approve» (spec + plan) / поправки к Assumptions — затем IMPLEMENT. Dual approve required.
