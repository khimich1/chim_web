# Spec: Side panels ученика и группы (замена accordion)

**Версия:** 0.2.0  
**Дата:** 2026-07-24  
**Статус:** ✅ approved (2026-07-24) — IMPLEMENT complete (Vitest); see [`tasks/students-hub-side-panels.md`](../../tasks/students-hub-side-panels.md)  
**Источник:** [`docs/ideas/students-hub-side-panels.md`](../ideas/students-hub-side-panels.md)  
**Родитель (shipped):** [`homework-templates-students-hub.md`](homework-templates-students-hub.md) — хаб + шаблоны; **UI accordion supersede** этим spec  
**Связано:** [`teacher-cabinet-ux.md`](teacher-cabinet-ux.md) §8.3 (drawer — этот документ = детализация для хаба); soft-delete / reset-password / groups / templates API as-is

---

## Assumptions (проверьте до PLAN)

Если не поправите — считаем принятыми:

1. **Открытие карточки ученика:** круглый **(i)** слева у строки **и** клик по **логину** (`student.email` в UI) делают одно и то же → один right sheet. Клик по остальным ячейкам строки (трек, stats…) **не** открывает панель. Сейчас в UI есть только клик по логину → accordion; **(i) — новый контрол**.
2. **Закрытие:** Escape, клик по backdrop, кнопка «Закрыть». Focus trap в sheet; при закрытии focus возвращается к триггеру ((i) или логин). Один открытый sheet за раз (ученик **или** группа).
3. **Не modal и не route** — overlay/sheet поверх `/teacher/students?tab=list|groups`, без navigate на `/teacher/students/[id]`.
4. **Содержимое sheet ученика (MVP):**
   - шапка: логин, трек, онбординг;
   - сводка stats из уже загруженных `TeacherStudentStats` на странице (без отдельного stats endpoint);
   - **история ДЗ** — assignments этого ученика (title, status, due); `cancelled` с видимой меткой;
   - **открытые** = filter `status === "in_progress"` (секция или фильтр в истории; не tutor sessions);
   - **Назначить ДЗ** = текущий flow: select шаблона + optional due + кнопка → `assignHomeworkTemplate`;
   - список / активные назначенные — тот же набор данных (история или фильтр «активные»);
   - **сброс пароля** = текущий `POST /api/students/{id}/reset-password`, temp password показать **один раз** в sheet;
   - **удаление** = текущий soft-delete (`DELETE` → `is_active=false`) + `window.confirm` (или эквивалент); после успеха sheet закрыть, список обновить;
   - **«Диалоги AI»** = UI-заглушка («Скоро» / пустое состояние), **без** `GET /api/tutor/students/{id}/sessions` и без любых tutor network calls.
5. **Данные ДЗ в карточке:** при открытии sheet FE вызывает существующий `GET /api/homework` (`listHomework`) и фильтрует по `student_id`. Teacher list **уже включает** `cancelled` (student list на бэке их скрывает — нам подходит teacher endpoint). Dedicated `GET /api/students/{id}/card` — **не** в этом релизе. Hard blocker не найден; если при PLAN/impl всплывёт (таймаут, слишком тяжёлый payload) — **Ask first**.
6. **Группы:** список групп остаётся на вкладке (create, счётчик). Клик по имени/строке группы → right sheet. Inline detail / «карточка под списком» (текущий `GroupsPanel`) убираем: без выбранного sheet — только список (+ create). После **создания** группы — открыть sheet новой группы (удобный дефолт).
7. **Состав группы:** dual-list — колонка **«В группе»** и **«Свободные»** (ученики без группы **или** уже в этой). Ученики в **другой** группе в «Свободные» не попадают (как сейчас: нельзя выбрать чужого члена без выхода). Перенос: кнопки «→ / ←» и/или клик + «Добавить/Убрать»; черновик локально; **«Сохранить состав»** → один `PUT .../members` (replace). DnD — out. Hint про «уже в других группах» допустим текстом вне dual-list (как сейчас blocked list).
8. **В sheet группы также:** rename (`PATCH`), назначить шаблон группе (fan-out), удалить группу — семантика API и revoke-on-remove **как сейчас**.
9. **Backend endpoints не меняем**, кроме фикса бага. Новых npm-зависимостей для drawer нет (CSS + `'use client'`). Shared `SidePanelShell` — по желанию (backdrop / Escape / focus), без UI-lib.
10. **Тесты:** обновить Vitest `StudentList` / `GroupsPanel` / `StudentsHub`; тесты open/close sheet, (i)+логин → один dialog, dual-list + save; AI-секция без mock/fetch tutor. Backend pytest — регрессия только если API трогаем (по умолчанию нет).
11. **Этот spec supersedes** UI-часть accordion из `homework-templates-students-hub.md` (§ accordion / Card UI) и детализирует drawer из `teacher-cabinet-ux.md` §8.3 для текущего хаба (шаблоны, не старый `/teacher/homework/new?studentId=`). «Открытые сессии» из cabinet UX в этом релизе = **homework `in_progress`**, не AI/tutor sessions.
12. **Narrow viewport:** sheet на всю ширину (или почти), backdrop остаётся; отдельный mobile redesign — out.

→ Поправьте нумерованные пункты, иначе после approve идём в PLAN с ними.

---

## 1. Objective

### Что строим

Замена accordion / inline-detail в хабе Ученики на **right sheets**:

1. Карточка ученика по **(i)** / логину.
2. Карточка группы по клику на группу + **dual-list** состава.

### Зачем

Таблица с разворотом вниз шумная; операционка (ДЗ, пароль, состав) удобнее сбоку, таблица остаётся обзором без потери контекста списка.

### Для кого

| Роль | Эффект |
|------|--------|
| **Преподаватель** | Быстрый доступ к админке ученика/группы без ухода со страницы |
| **Ученик** | Без изменений API/поведения |

### Baseline (as-is)

| Место | Сейчас |
|-------|--------|
| `StudentList.tsx` | Клик по логину → accordion-row: assign / reset / delete; нет (i); нет истории ДЗ / AI |
| `GroupsPanel.tsx` | Список + inline detail с checkbox-составом; auto-select первой группы |

### User stories + acceptance

| ID | Story | Acceptance |
|----|--------|------------|
| US-SP-1 | Открыть карточку ученика по (i) | Клик (i) → right sheet с логином; строка таблицы **не** expand |
| US-SP-2 | Открыть карточку по логину | Клик логин → **тот же** sheet, что и (i) |
| US-SP-3 | Закрыть sheet | Escape / backdrop / «Закрыть» → sheet исчез; focus на триггере |
| US-SP-4 | Назначить ДЗ из sheet | Select шаблон → Назначить → assignment у ученика; успех в UI |
| US-SP-5 | История ДЗ | В sheet видны assignments ученика (title, status, due); cancelled с меткой |
| US-SP-6 | Сброс пароля | Как сейчас: кнопка → temp password один раз в sheet |
| US-SP-7 | Удалить ученика | Confirm → soft-delete; sheet закрывается; нет в списке |
| US-SP-8 | Заглушка AI | Секция «Диалоги AI» видна; **ноль** network к tutor sessions |
| US-SP-9 | Открыть группу в sheet | Клик группа → right sheet; inline expand/detail под списком нет |
| US-SP-10 | Dual-list состава | «В группе» / «Свободные»; перенос; Сохранить → `PUT members`; revoke-on-remove как сейчас |
| US-SP-11 | Assign / rename / delete группы | Из sheet; поведение API без регрессии |

---

## 2. Tech Stack

| Слой | Стек |
|------|------|
| Frontend | Next.js App Router, React `'use client'`, Vitest + RTL |
| Backend | Без обязательных изменений (FastAPI endpoints as-is) |
| API (reuse) | `GET /api/homework`, templates assign, students delete/reset, groups CRUD/members |
| UI | Собственный right sheet (fixed panel + backdrop), без новой UI-lib |

---

## 3. Commands

```bash
cd frontend
npm run test -- StudentList GroupsPanel StudentsHub SidePanelShell
npm run lint
npm run dev

cd backend
# только если трогали API; иначе smoke не обязателен для merge UI-среза
pytest tests/test_teacher_groups.py tests/test_students.py -q
```

Dev: хаб `http://localhost:3000/teacher/students` (FastAPI `:8000`).

---

## 4. Project Structure

```
frontend/components/students/
  StudentList.tsx          # таблица + (i)/логин → open sheet (без accordion)
  StudentSidePanel.tsx     # NEW: содержимое drawer ученика
  GroupsPanel.tsx          # список групп → open sheet (без inline detail)
  GroupSidePanel.tsx       # NEW: drawer группы + dual-list
  SidePanelShell.tsx       # NEW (рекомендуется): shared backdrop / Escape / focus / a11y
  *.test.tsx               # рядом с компонентами

frontend/lib/api/
  homework.ts              # listHomework — reuse
  students.ts / groups.ts / templates.ts  # as-is

docs/ideas/students-hub-side-panels.md
docs/specs/students-hub-side-panels.md   # этот файл (canonical)
tasks/students-hub-side-panels.md        # PLAN ready (pending spec approve)
```

---

## 5. Code Style

```tsx
// Триггеры открывают один sheet; логин и (i) — один handler
function openStudent(id: string) {
  setOpenStudentId(id);
}

<button
  type="button"
  aria-label={`Информация об ученике ${login}`}
  onClick={() => openStudent(student.id)}
>
  (i)
</button>
<button
  type="button"
  aria-haspopup="dialog"
  onClick={() => openStudent(student.id)}
>
  {login}
</button>

// Sheet shell
<aside
  role="dialog"
  aria-modal="true"
  aria-labelledby="student-sheet-title"
  className="fixed inset-y-0 right-0 z-50 …"
>
  …
</aside>
```

- Русские UI-строки как в кабинете (`chem-*` классы / существующие паттерны).
- Не дублировать бизнес-валидацию backend (трек-mismatch 422 → показать `ApiError.message`).
- Один источник открытого id: `openStudentId: string | null` / `openGroupId: string | null` (взаимоисключающие).

---

## 6. Testing Strategy

| Уровень | Что |
|---------|-----|
| Vitest | (i) и логин открывают dialog с тем же заголовком/логином; Escape / backdrop / «Закрыть» вызывают close; в DOM нет accordion `role="region"` под строкой; dual-list перенос + Save → `replaceTeacherGroupMembers` с ожидаемым id[]; секция AI без вызова tutor API |
| Backend | Регрессия groups/students **без** новых тестов, если API не трогаем |
| Manual / browser | Tab `list` + `groups`; keyboard Escape; narrow width sheet; assign / reset / delete smoke |

Coverage: затронутые компоненты — зелёные тесты до merge среза. Глобальный % не раздувать.

---

## 7. Boundaries

### Always

- Accordion-expand убрать из list; inline group detail убрать с вкладки Groups.
- a11y: `role="dialog"`, `aria-modal="true"`, Escape, focus trap, focus return.
- Сохранить текущую семантику reset-password (temp once) и soft-delete.
- Dual-list уважает правило ученик ∈ 0..1 группе.
- История ДЗ через FE-filter `GET /api/homework`, пока не одобрен `/card`.

### Ask first

- Новый aggregate endpoint `/api/students/{id}/card`.
- Реальная подгрузка AI-сессий / transcripts.
- Invite-link вместо temp password.
- Новые npm-зависимости для drawer.
- Изменение revoke / fan-out / soft-delete семантики.

### Never

- Navigate на `/teacher/students/[id]` для этой карточки.
- Грузить tutor sessions/transcripts «заодно».
- DnD состава в MVP.
- Менять backend «на всякий случай» без бага.
- Стартовать IMPLEMENT до approve этого spec (PLAN уже есть в `tasks/` по явному запросу; код — только после approve).

---

## 8. Success Criteria

- [ ] Нет accordion-разворота в «Ученики» и нет inline detail под списком «Группы».
- [ ] (i) и логин открывают один right sheet ученика.
- [ ] В sheet ученика: stats, история ДЗ (с cancelled), назначить, reset, delete, AI-заглушка без tutor fetch.
- [ ] Группа открывается в right sheet с dual-list «в группе / свободные»; Save → `PUT members`.
- [ ] Vitest зелёные для затронутых компонентов.
- [ ] Назначение / reset / delete / members в UI без регрессии семантики API.

---

## 9. Out of scope

- Реальные AI-диалоги / transcript / tutor sessions API.
- `GET /api/students/{id}/card`.
- Invite-link / «перевыпуск приглашения» отличный от reset-password.
- Chrome / Конструктор / clipboard / lightbox (другие specs).
- Переработка вкладки «Добавить».
- DnD состава; batch multi-select учеников вне группы.

---

## 10. Open Questions

Нет блокирующих. Решения пользователя зафиксированы в Assumptions 1–12.

**Approve spec?** → затем IMPLEMENT по [`tasks/students-hub-side-panels.md`](../../tasks/students-hub-side-panels.md) (PLAN уже готов; при смене Assumptions после approve — обновить план).

---

## 11. Amendment к предыдущим specs

| Было | Станет (этот релиз) |
|------|---------------------|
| `homework-templates-students-hub`: accordion по логину; история ДЗ / AI — out; состав группы — checkbox в expand | Right sheet по (i) **и** логину; история ДЗ — **in**; AI — **заглушка**; dual-list в group sheet |
| `teacher-cabinet-ux` §8.3: drawer + опционально `/card`; «открытые сессии»; assign через homework/new | Drawer на хабе; `/card` отложен; открытые = homework `in_progress`; assign = шаблоны (как shipped hub) |

Краткий указатель стоит добавить в шапку `homework-templates-students-hub.md` после approve этого spec (чтобы accordion не читали как актуальный UI-target).
