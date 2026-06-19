# User Stories: Онбординг ученика (Sprint backlog)

**Связано с:** [PRD: Student Onboarding](./prd-student-onboarding.md)  
**Дата:** 19.06.2026  
**Статус:** Sprint 1–2 реализованы (v1.0)

---

## Epic: Student Onboarding v1

**Outcome:** ≥70% новых учеников совершают целевое действие за 24 часа после первого входа.

---

## Sprint 1 — Backend + Welcome (P0) ✅

### US-1.1 Миграция onboarding-полей ✅

**Acceptance criteria:**
- [x] Поля: `first_login_at`, `onboarding_completed_at`, `onboarding_checklist` (JSON)
- [x] Миграция `010_student_onboarding` — существующие ученики помечены `onboarding_completed_at = now()`
- [x] Alembic upgrade/downgrade проходит

**Файлы:** `alembic/versions/010_student_onboarding.py`, `models/student_profile.py`

---

### US-1.2 API онбординга ✅

**Acceptance criteria:**
- [x] `GET /api/students/me/onboarding` → статус, чеклист, `needs_welcome`
- [x] `GET /api/students/me/onboarding/welcome` → + recommended_action
- [x] `PATCH /api/students/me/onboarding` → `complete_welcome`, `mark_step`
- [x] При первом GET выставляется `first_login_at`, `checklist.login = true`
- [x] Только role=student
- [x] Тесты: `test_onboarding_api.py`
- [x] Analytics: события `onboarding_*` в activity ledger

---

### US-1.3 Статус активации для преподавателя ✅

**Acceptance criteria:**
- [x] `StudentRead`: `first_login_at`, `onboarding_completed_at`, `is_activated`
- [x] `is_activated` = checklist.first_action **или** learning activity event
- [x] Колонка в списке учеников

---

### US-1.4 Welcome-экран ✅

**Acceptance criteria:**
- [x] `/student/welcome`
- [x] Primary CTA: ДЗ или диагностический тест
- [x] «Позже» → complete_welcome → `/student`
- [x] CTA → PATCH + переход

---

### US-1.5 Редирект на welcome ✅

**Acceptance criteria:**
- [x] `StudentOnboardingGate` в layout
- [x] Исключение `/student/welcome`

---

## Sprint 2 — Чеклист + полировка ✅

### US-2.1 Чеклист на дашборде ✅

- [x] 3 шага на `/student`
- [x] Скрывается при 3/3
- [x] `mark_step: lecture` на странице темы учебника

### US-2.2 TrackExplainer ✅

- [x] Блок на welcome

### US-2.3 Авто-mark first_action ✅

- [x] Backend hook при создании test session
- [x] Backend hook при `GET /api/homework/{id}` (student)

---

## Backlog (P1)

| ID | Story | SP | Статус |
|----|-------|-----|--------|
| US-3.1 | Magic link | 8 | ❌ |
| US-3.2 | first_action при создании ученика | 5 | ❌ |
| US-3.3 | Видео-приветствие | 3 | ❌ |
| US-3.4 | Coach marks | 5 | ❌ |
| US-3.5 | Дашборд метрик activation (SQL/Metrika) | 3 | ❌ |

---

## Definition of Done (Epic)

- [x] P0 acceptance criteria
- [x] pytest + vitest
- [x] Миграция для старых учеников
- [x] Analytics events
- [ ] Custdev 3+ интервью
