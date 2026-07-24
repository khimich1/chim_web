# Students hub: side panels (ученик / группа)

**Дата:** 2026-07-24  
**Статус:** idea one-pager → spec draft awaiting approve; PLAN ready pending approve → [`tasks/students-hub-side-panels.md`](../../tasks/students-hub-side-panels.md)  
**Canonical spec:** [`docs/specs/students-hub-side-panels.md`](../specs/students-hub-side-panels.md)  
**Связано:** [`homework-templates-students-hub.md`](../specs/homework-templates-students-hub.md) (accordion UI — **supersede**); [`teacher-cabinet-ux.md`](../specs/teacher-cabinet-ux.md) (§8.3 drawer)

## Problem Statement

How might we дать преподавателю открыть операционную карточку ученика или группы **справа**, не раздувая таблицу accordion’ом и не уходя со страницы?

## Recommended Direction

**Right sheet вместо accordion / inline group detail.**

- Вкладка **Ученики**: круглый **(i)** слева у строки **и** клик по **логину** → один и тот же right sheet.
- В карточке ученика: stats, история ДЗ / открытые (`in_progress`), назначить шаблон, сброс пароля (temp once), soft-delete, **заготовка** «Диалоги AI» (без загрузки чатов).
- Вкладка **Группы**: клик по группе → right sheet; состав — **dual-list** «в группе / свободные»; Save → `PUT members`.

## Key Assumptions

- Accordion в `StudentList` и inline detail в `GroupsPanel` убираем; без `/teacher/students/[id]`.
- «Перевыпуск» = текущий `reset-password` + temp один раз (не invite-link).
- AI — только UI-заглушка; tutor sessions не грузим.
- История ДЗ: FE-filter `GET /api/homework` по `student_id`; `/card` — later (ask first).
- Backend as-is; без новых UI-зависимостей.

## MVP Scope

**In:** sheets ученика и группы; (i)+логин; dual-list; история ДЗ; placeholder AI.  
**Out:** реальные AI-сессии; invite-link; `/card`; route `[id]`; DnD состава.

## Success Looks Like

Преподаватель: (i) или логин → панель справа с админкой; группа → dual-list → сохранить состав; таблица/список остаются обзором.
