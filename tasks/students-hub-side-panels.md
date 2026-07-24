# Implementation Plan: Side panels ученика и группы

> **PLAN from spec v0.2.0; if assumptions change after approve, update plan.**  
> Spec status: ✅ approved (2026-07-24). IMPLEMENT complete (Vitest green; manual smoke pending human).

**Источник:** [`docs/specs/students-hub-side-panels.md`](../docs/specs/students-hub-side-panels.md) v0.2.0 · idea: [`docs/ideas/students-hub-side-panels.md`](../docs/ideas/students-hub-side-panels.md)  
**Дата плана:** 2026-07-24  
**Статус:** ✅ IMPLEMENT done (automated) — manual smoke checklist below  
**Skills:** incremental-implementation → TDD → frontend-ui-engineering  
**Коммиты:** только по явной просьбе пользователя  
**Backend:** без изменений (as-is APIs)

### Progress

| Task | Статус |
|------|--------|
| SP-1 SidePanelShell (a11y) + tests | ✅ done |
| SP-2 StudentList → sheet: (i)+login, assign/reset/delete | ✅ done |
| SP-3 Homework history в StudentSidePanel | ✅ done |
| SP-4 AI placeholder section | ✅ done |
| SP-5 GroupsPanel list-only + GroupSidePanel dual-list | ✅ done |
| SP-6 Group assign/rename/delete + create opens sheet | ✅ done |
| SP-7 Vitest alignment + manual smoke checkpoint | ✅ done (automated); manual ⬜ |

---

## Overview

Заменить accordion в `StudentList` и inline detail в `GroupsPanel` на **right sheets** поверх `/teacher/students` без новых routes и без `/card` endpoint. Ученик: **(i)** + клик по логину → один sheet (stats, история ДЗ через `listHomework` + FE-filter, назначить шаблон, reset-password, soft-delete, AI-заглушка). Группа: клик → sheet с dual-list «В группе» / «Свободные», Save → `PUT .../members`; rename / assign / delete — в том же sheet. Shared `SidePanelShell` (backdrop, Escape, focus trap, focus return). API и npm-deps — as-is.

**Baseline:** hub shipped (tabs + accordion + checkbox members). Untracked red test: `SidePanelShell.test.tsx` уже импортирует несуществующий `SidePanelShell`.

---

## Architecture Decisions

| Решение | Выбор | Почему |
|---------|--------|--------|
| Sheet vs route / modal-page | Fixed right panel + backdrop, `role="dialog"` `aria-modal="true"` | Spec; таблица остаётся обзором; нет `/teacher/students/[id]` |
| Shared shell | `SidePanelShell` first | Один a11y-контракт; уже есть падающий Vitest |
| Focus / Escape | Shell owns Escape, backdrop close, focus trap, return focus to trigger | Spec US-SP-3; ориентир — `useReferenceDialog`, но shell должен делать **trap**, не только Escape |
| Open state | `openStudentId` / `openGroupId` внутри list/panel (tabs unmount sibling) | Один sheet на вкладку; hub-level coordination не нужен |
| Student triggers | Round **(i)** + login button → один `openStudent(id)` | Spec assumption 1; остальные ячейки строки не открывают |
| Accordion removal | Убрать `expandedId` + `role="region"` row | Spec Always |
| Homework in card | On open: `listHomework()` → filter `student_id`; show cancelled; filter/section `in_progress` | No `/card`; teacher list includes cancelled |
| Stats | From props `TeacherStudentStats` already on page | No extra stats fetch |
| AI section | Static placeholder only | Zero tutor network calls |
| Groups list | List + create only; **no** auto-select first group; no inline `<section>` detail | Spec assumption 6 |
| Dual-list | Local draft ids; «Сохранить состав» → `replaceTeacherGroupMembers` | Same replace semantics / revoke as today |
| Create group | After create → open sheet for new group | Spec convenience default |
| Backend / deps | No API changes; no new drawer npm packages | Spec assumptions 9–10 |

---

## Dependency graph

```
SP-1 SidePanelShell (+ existing SidePanelShell.test.tsx green)
 │
 ├── SP-2 StudentList: (i)+login → StudentSidePanel
 │     │   (assign / reset / delete migrated; accordion gone)
 │     │
 │     ├── SP-3 Homework history (listHomework filter)
 │     │     │
 │     │     └── SP-4 AI placeholder (no tutor fetch)
 │     │
 │     └── (parallel-safe after SP-2 green)
 │
 └── SP-5 GroupsPanel list-only + GroupSidePanel dual-list + Save
           │
           └── SP-6 Rename / assign / delete in sheet; create opens sheet
                     │
                     └── SP-7 Vitest sweep + manual smoke notes
```

**Safe parallel after SP-1:** student path (SP-2→4) and groups path (SP-5→6) can run in separate sessions if coordinated on `SidePanelShell` API only.  
**Recommended sequential for one agent:** SP-1 → SP-2 → SP-3 → SP-4 → SP-5 → SP-6 → SP-7.

**Demo-минимум:** SP-1 → SP-2 (teacher opens student sheet and can assign/reset/delete).

---

## Task List

### Phase 1: Foundation + student sheet core

---

## Task SP-1: Shared SidePanelShell (a11y) + tests

**Description:** Implement `SidePanelShell` so the existing Vitest file passes and a11y matches spec: when `open`, render backdrop + right `aside`/`div` dialog with title; Escape and backdrop close call `onClose`; closed → nothing; focus moves into panel on open and returns to trigger on close; basic focus trap while open. No UI-lib. CSS: fixed right, full/near-full width on narrow viewport.

**Acceptance criteria:**
- [ ] `SidePanelShell.test.tsx` green (open dialog, Escape, backdrop/close control, closed = no dialog)
- [ ] Props at least: `open`, `title`, `onClose`, `children`; optional `titleId` / `initialFocusRef` / `returnFocusRef` as needed
- [ ] `role="dialog"`, `aria-modal="true"`, labelled by title; Escape closes; body scroll locked while open

**Verification:**
- [ ] `cd frontend && npm run test -- SidePanelShell`
- [ ] Manual (optional): render in Story/dev page or temporary — Escape + Tab stay in panel

**Dependencies:** None

**Files likely touched:**
- `frontend/components/students/SidePanelShell.tsx` (new)
- `frontend/components/students/SidePanelShell.test.tsx` (exists; extend only if trap/return-focus need asserts)

**Estimated scope:** S (1–2 files)

---

## Task SP-2: StudentList → right sheet (i)+login; migrate assign/reset/delete

**Description:** Replace accordion with sheet. Add round **(i)** control left of login; login and (i) share one open handler. Render `StudentSidePanel` via `SidePanelShell` with header (login, track, onboarding), stats from props, and migrated flows: template assign + optional due, reset-password (temp once), soft-delete + confirm → close sheet + `router.refresh()`. Remove accordion row / `role="region"`. Update StudentList tests accordingly.

**Acceptance criteria:**
- [ ] Click (i) or login → one dialog titled/showing that student’s login; no table expand
- [ ] Click track/stats cells does **not** open sheet
- [ ] Assign / reset / delete behave as today (API + UI feedback); delete closes sheet
- [ ] No `role="region"` accordion under the row
- [ ] Close: Escape / backdrop / «Закрыть» (via shell)

**Verification:**
- [ ] `cd frontend && npm run test -- StudentList SidePanelShell`
- [ ] Manual: `/teacher/students?tab=list` — open via (i) and login; assign smoke if templates exist

**Dependencies:** SP-1

**Files likely touched:**
- `frontend/components/students/StudentList.tsx`
- `frontend/components/students/StudentSidePanel.tsx` (new)
- `frontend/components/students/StudentList.test.tsx`

**Estimated scope:** M (3–4 files)

---

### Checkpoint: After SP-1–SP-2

- [ ] `npm run test -- SidePanelShell StudentList` green
- [ ] Accordion gone; sheet opens from (i) and login
- [ ] Assign / reset / delete still work in sheet
- [ ] Spec still draft? Confirm approve before deeper slices if required by process
- [ ] Human glance OK before SP-3–4 (history + AI)

---

### Phase 2: Student sheet content

---

## Task SP-3: Homework history in StudentSidePanel

**Description:** On sheet open, call existing `listHomework()`, filter by `student.id`. Show history: title, status, due; mark `cancelled` visibly; support «открытые» as `status === "in_progress"` (section or filter). Loading / empty / error states. No new endpoint. After successful assign, refresh the list in-panel (or re-fetch).

**Acceptance criteria:**
- [ ] Opening sheet triggers one `listHomework` (mocked in tests); UI lists only this student’s assignments
- [ ] Cancelled assignments visible with clear label
- [ ] In-progress assignments identifiable (section or filter)
- [ ] Assign success updates history without leaving sheet

**Verification:**
- [ ] `cd frontend && npm run test -- StudentList` (and `StudentSidePanel` if separate test file)
- [ ] Manual: student with mixed statuses — history shows cancelled + in_progress

**Dependencies:** SP-2

**Files likely touched:**
- `frontend/components/students/StudentSidePanel.tsx`
- `frontend/components/students/StudentList.test.tsx` and/or `StudentSidePanel.test.tsx` (new)
- (read-only reuse) `frontend/lib/api/homework.ts`

**Estimated scope:** S–M (2–3 files)

---

## Task SP-4: AI placeholder section

**Description:** Add «Диалоги AI» section in student sheet: empty / «Скоро» placeholder. Assert in tests that no tutor/sessions API module is called (do not mock tutor endpoints — ensure they are never imported/invoked).

**Acceptance criteria:**
- [ ] Section visible in open student sheet
- [ ] Zero network/API calls to tutor sessions
- [ ] Vitest covers presence + no tutor fetch

**Verification:**
- [ ] `cd frontend && npm run test -- StudentList StudentSidePanel`
- [ ] Manual: open sheet — see placeholder; Network tab has no tutor sessions request

**Dependencies:** SP-2 (can land after or with SP-3; prefer after SP-3 to keep history slice focused)

**Files likely touched:**
- `frontend/components/students/StudentSidePanel.tsx`
- `frontend/components/students/StudentList.test.tsx` or `StudentSidePanel.test.tsx`

**Estimated scope:** S (1–2 files)

---

### Checkpoint: After SP-3–SP-4

- [ ] Student sheet: stats + history + assign + reset + delete + AI placeholder
- [ ] `npm run test -- StudentList SidePanelShell` green
- [ ] No tutor API in Network on open
- [ ] Review before groups rewrite

---

### Phase 3: Groups sheet

---

## Task SP-5: GroupsPanel list-only + GroupSidePanel dual-list

**Description:** Strip inline detail from `GroupsPanel`: keep header, create button, group list. Remove auto-select of first group on load. Click group name/row → open `GroupSidePanel` in `SidePanelShell`. Dual-list: «В группе» / «Свободные» (unassigned **or** already in this group); students in **other** groups only in blocked hint, not in free list. Transfer via →/← and/or Add/Remove; draft local; «Сохранить состав» → `replaceTeacherGroupMembers` with full id[]. Update GroupsPanel tests (no inline `region` with checkboxes).

**Acceptance criteria:**
- [ ] With groups loaded and no click: **no** inline detail section under list
- [ ] Click group → dialog with dual-list; Save sends expected member id[]
- [ ] Other-group students not selectable in free list; hint text OK
- [ ] Closing sheet returns to list-only

**Verification:**
- [ ] `cd frontend && npm run test -- GroupsPanel SidePanelShell`
- [ ] Manual: `/teacher/students?tab=groups` — click group, move members, save

**Dependencies:** SP-1 (independent of SP-2–4 structurally)

**Files likely touched:**
- `frontend/components/students/GroupsPanel.tsx`
- `frontend/components/students/GroupSidePanel.tsx` (new)
- `frontend/components/students/GroupsPanel.test.tsx`

**Estimated scope:** M (3–4 files)

---

## Task SP-6: Group assign / rename / delete in sheet; create opens sheet

**Description:** Move rename, template assign (group fan-out), and delete into `GroupSidePanel` (same API semantics as current GroupsPanel). After **create**, open sheet for the new group (not leave list-only). On delete success: close sheet, refresh list (no auto-open another group unless product wants — prefer list-only after delete to match «no auto-select»).

**Acceptance criteria:**
- [ ] Rename / assign / delete work from sheet without regression vs current API calls
- [ ] Create group → sheet opens for new group
- [ ] Delete → confirm → group gone, sheet closed
- [ ] Empty group cannot assign (same guard as today)

**Verification:**
- [ ] `cd frontend && npm run test -- GroupsPanel`
- [ ] Manual: create → sheet opens; rename; assign; delete

**Dependencies:** SP-5

**Files likely touched:**
- `frontend/components/students/GroupSidePanel.tsx`
- `frontend/components/students/GroupsPanel.tsx`
- `frontend/components/students/GroupsPanel.test.tsx`

**Estimated scope:** M (2–3 files)

---

### Checkpoint: After SP-5–SP-6

- [ ] Groups: list-only + sheet dual-list + rename/assign/delete + create→open
- [ ] `npm run test -- GroupsPanel SidePanelShell` green
- [ ] Revoke-on-remove / fan-out semantics unchanged (UI-level; no backend change)

---

### Phase 4: Polish / verify

---

## Task SP-7: Vitest alignment + manual smoke notes

**Description:** Sweep remaining hub tests (`StudentsHub`, any leftover accordion/region assertions). Ensure AI tests don’t introduce tutor mocks. Document short manual smoke checklist in this plan’s checkpoint below (no app code). Run lint on touched FE files.

**Acceptance criteria:**
- [ ] `StudentList` / `GroupsPanel` / `StudentsHub` / `SidePanelShell` tests green
- [ ] No obsolete accordion assertions
- [ ] Manual smoke checklist filled (pass/fail notes)

**Verification:**
- [ ] `cd frontend && npm run test -- StudentList GroupsPanel StudentsHub SidePanelShell`
- [ ] `cd frontend && npm run lint`
- [ ] Manual smoke (below)

**Dependencies:** SP-2…SP-6

**Files likely touched:**
- `frontend/components/students/*.test.tsx`
- `frontend/components/students/StudentsHub.test.tsx` (only if assertions need update)
- `tasks/students-hub-side-panels.md` (checkpoint notes only)

**Estimated scope:** S (1–3 files)

---

### Checkpoint: Complete (after SP-7)

**Automated** (2026-07-24)
- [x] `cd frontend && npm run test -- StudentList GroupsPanel StudentsHub SidePanelShell` → **22 passed**
- [x] Touched `components/students/*` eslint: no new errors (project-wide lint still has pre-existing ContentBlocksEditor error)
- [x] Backend pytest **skipped** (API untouched)

**Manual smoke** (`http://localhost:3000/teacher/students`, API `:8000`) — pending human
- [ ] Tab list: (i) and login open same sheet; Escape / backdrop / Закрыть
- [ ] Assign template; reset password shows temp once; delete + confirm closes sheet
- [ ] History shows cancelled + in_progress; AI section visible; Network: no tutor sessions
- [ ] Tab groups: no inline detail; click → dual-list; Save members; rename; assign; delete
- [ ] Create group opens sheet; narrow viewport sheet nearly full width
- [ ] Ready for code-review-and-quality before merge

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Spec assumptions change after approve | Med | Banner at top of plan; re-diff tasks vs Assumptions 1–12 before SP-1 |
| `listHomework` heavy / slow for teachers with many assignments | Med | FE filter only for MVP; if timeout/UX bad → **Ask first** before `/card` |
| Focus trap incomplete vs overlay patterns | Med | Implement in SP-1 with tests; mirror Escape/overflow from `useReferenceDialog`, add trap |
| GroupsPanel rewrite breaks many tests at once | Med | SP-5 dual-list first; SP-6 ops second; keep API mocks same |
| Accidental tutor API import «for later» | Low | SP-4 + test asserting no tutor call; Never in spec |
| Scope creep into invite-link / DnD / route `[id]` | Low | Out of scope list; Ask first table in spec |
| Mutual open student+group | Low | Tabs unmount; one `open*Id` per panel |

---

## Open Questions

Нет блокирующих для PLAN. Spec Open Questions пусты; Assumptions 1–12 accepted for planning.

Non-blocking (resolve only if approve comments change them):
- After group delete: list-only (plan default) vs auto-open next group — plan chooses list-only to match «no auto-select».
- History UI: separate «Открытые» section vs status filter chips — implementer choice within SP-3 acceptance.

---

## Parallelization (optional)

| Track A (student) | Track B (groups) |
|-------------------|------------------|
| After SP-1: SP-2 → SP-3 → SP-4 | After SP-1: SP-5 → SP-6 |
| Merge before SP-7 | |

Coordinate: do not both edit `SidePanelShell` after SP-1 lands.

---

## Recommended first implement task

**SP-1: SidePanelShell** — unblocks both tracks; `SidePanelShell.test.tsx` already red and defines the contract.
