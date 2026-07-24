# Конструктор + отзыв ДЗ в хабе Ученики

**Дата:** 2026-07-24  
**Статус:** idea one-pager → spec draft + PLAN ready — pending dual approve (spec + plan) before IMPLEMENT  
**Canonical spec:** [`docs/specs/constructor-nav-and-homework-revoke.md`](../specs/constructor-nav-and-homework-revoke.md)  
**Plan:** [`tasks/constructor-nav-and-homework-revoke.md`](../../tasks/constructor-nav-and-homework-revoke.md)  
**Связано:** [`students-hub-side-panels.md`](../specs/students-hub-side-panels.md), [`homework-templates-students-hub.md`](../specs/homework-templates-students-hub.md), [`teacher-header-chrome.md`](../specs/teacher-header-chrome.md) (rename «Темы» был out)

## Problem Statement

How might we дать преподавателю в хабе «Ученики» видеть историю назначений группе так же, как у ученика, снимать ошибочные/тестовые раздачи корзиной (несданные; у группы — у всех членов) с окном «Вернуть» 30 с, и не путать раздел кастомных тем с вкладкой «Темы» — переименовав nav в «Конструктор».

## Recommended Direction

**D1 — один MVP:** rename nav + история раздач в group sheet + явный cancel/restore (корзина, 30s undo) в student и group sheets.

1. **Nav:** «Темы» → **«Конструктор»** (`aria-label` / title: «Конструктор заданий»). Страница `/teacher/themes` — в том же смысле. Вкладка «Темы» у ученика в `TestsPicker` — **не трогаем**.
2. **Group sheet:** история раздач по образцу student sheet; **одна строка = одна групповая волна**; после assign/revoke — **сразу refresh**.
3. **Отзыв:** иконка корзины; ученик — только его assignment; группа — все несданные копии волны; сданные не трогаем; undo 30 с; у ученика без notify об отзыве — ДЗ просто исчезает из списка.

## Key Assumptions

- Undo = immediate `cancelled` + restore ≤30 с (server `cancelled_at`); hard-DELETE — out.
- «Насовсем» = навсегда `cancelled` в teacher history.
- Student `homework_assigned` notifications нет в модели — «пропасть» = list / resume / recommended actions.
- Scope: rename + group history/revoke + student revoke + cancel/restore API — **один MVP**.

## MVP Scope

**In:** D1 целиком.  
**Out:** hard delete; undo >30 с; notify ученику об отзыве; per-member pick в группе; сущность GroupAssignment; rename «Темы» у ученика.

## Success Looks Like

Преподаватель видит «Конструктор» в nav; в sheet группы — история раздач; корзина снимает несданные (у группы — у всех); 30 с можно вернуть; ученик больше не видит отозванное ДЗ.
