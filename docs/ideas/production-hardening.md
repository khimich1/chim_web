# Production Hardening: Phase 17 + Multi-teacher (Variant A)

**Проект:** chim_web  
**Дата:** 2026-06-21  
**Статус:** согласовано → Tasks 92–99 в `tasks/plan.md`

---

## Problem Statement

**HMW:** Как перевести chim_web с «MVP для одного репетитора» на **один deployable инстанс для N репетиторов**, сохранив maintainability (CI, типы, E2E) и **доказав** изоляцию данных — без SaaS-сложности и без переписывания архитектуры?

---

## Recommended Direction

Два трека одного слоя «production readiness»:

| Трек | Суть | Deliverable |
|------|------|-------------|
| **Multi-teacher A** | `teacher_id` = tenant boundary; CLI provisioning | Доки + IDOR test suite |
| **Phase 17** | CI, RAG, рефакторинг, security, E2E | Инфра под защитой IDOR-тестов |

**Multi-teacher:** CLI `seed_teacher` для N аккаунтов, без invite/admin UI.  
**Phase 17:** themes `task_count`, mypy/openapi-typescript в CI, RAG pg-only, TestSession adapters, rate limit, Playwright smoke.

**Cross-tenant by design (не баг):**

- Global leaderboard (`GET /api/leaderboard`) — ученики разных репетиторов соревнуются
- Content SQLite (ЕГЭ/ОГЭ, учебник) и RAG lecture index — shared read-only

---

## Architecture: три слоя данных

```
Shared (все teachers)          Tenant (teacher_id)
─────────────────────          ───────────────────
Content SQLite                 Students + profiles
RAG lecture index              Homework + submissions
Global leaderboard             Custom themes/tasks
                               Uploads + tutor sessions
                               Notifications
```

Ограничение «один teacher на инстанс» — **только в доках/CLI**, не в схеме БД.

---

## Key Assumptions to Validate

- [ ] Teacher B не может GET/PATCH чужие homework, themes, students, notifications
- [ ] Teacher B не может читать uploads/tutor sessions учеников teacher A
- [ ] Student видит только темы/ДЗ своего `teacher_id`
- [ ] TestSession refactor (Task 97) не ломает homework ownership
- [ ] 60 мин access TTL не обрывает длинный тест (Stepik ≤ ~2 ч) — при необходимости 120 мин
- [ ] Репетиторы согласны с глобальным рейтингом

---

## MVP Scope

### Track A — Multi-teacher (Tasks 92–93)

**Внутри:**

- SPEC §3: multi-teacher CLI, убрать «один преподаватель на инстанс»
- `seed_teacher.py` docstring + AGENTS.md
- `tests/multi_teacher/test_isolation.py` — единый IDOR checklist
- Ручной smoke: 2 teachers, по 1–2 student, cross-access → 403/404

**Снаружи:**

- Invite / self-registration teacher
- Admin UI, per-teacher leaderboard
- Org/school, billing, transfer student между teachers

### Track B — Phase 17 (Tasks 94–99)

| Task | Срез |
|------|------|
| 94 | `GET /api/teacher/themes` + `task_count`, убрать N+1 frontend |
| 95 | CI: `mypy app/services/ app/api/` + openapi-typescript drift check |
| 96 | RAG: metadata + vectors в PG; json/Chroma вне hot path |
| 97 | TestSessionService → exam / custom / homework adapters (**после Task 93**) |
| 98 | Rate limit login + tutor; access TTL 60 мин |
| 99 | Playwright smoke: login → 1 шаг теста → submit ДЗ |

---

## Not Doing (and Why)

| Не делаем | Почему |
|-----------|--------|
| Refresh tokens | Короткий access + rate limit достаточно для MVP |
| Full `mypy app/` | LangChain false positives; расширять постепенно |
| Redis rate limiter | Single-node VPS |
| Per-teacher RAG | Shared lectures by design |
| Invite-код teacher | CLI-only по выбору Variant A |
| Отдельный Docker на teacher | Variant A решает через `teacher_id` |

---

## IDOR Audit Checklist

Приоритет для `tests/multi_teacher/test_isolation.py`:

| Зона | Endpoints | Ожидание |
|------|-----------|----------|
| Students | `GET/POST /api/students` | B не видит учеников A |
| Homework | `GET/PATCH /api/homework/{id}`, submit, feedback | 403/404 |
| Themes | CRUD `/api/teacher/themes/*`, tasks | 404 |
| Tutor | sessions by student_id | 403 |
| Uploads | `GET /api/uploads/images/{id}`, audio | 403 |
| Notifications | `PATCH /api/notifications/{id}/read` | 403 |
| Stats | `GET /api/teacher/students/stats` | только свои |

**Намеренно cross-tenant:** `GET /api/leaderboard`

---

## Sequencing

```
Task 92 docs ──→ Task 93 IDOR tests ──→ Task 97 TestSession adapters
     │                    │
     └──── Task 94 task_count (parallel)
              Task 95 CI (parallel)
              Task 96 RAG
              Task 98 auth
              Task 99 Playwright
```

Phase 16 (ЕГЭ 29–34) — параллельно, если не трогает mixed TestSession paths.

---

## Open Questions

- Лимит teachers на инстанс (`MAX_TEACHERS` env)?
- Display «репетитор» в leaderboard (read-only)?
- Политика `is_active=false` для teacher — что с учениками?

---

## Handoff

| Шаг | Skill | Артефакт |
|-----|-------|----------|
| AC в SPEC | spec-driven-development | §3 multi-teacher |
| Tasks 92–99 | planning-and-task-breakdown | `tasks/plan.md` |
| Срезы | incremental-implementation | коммиты по task |
| IDOR | test-driven-development | RED → GREEN |

---

## Оценка

| Работа | Оценка |
|--------|--------|
| Tasks 92–93 (multi-teacher) | ~2 дня |
| Tasks 94–99 (Phase 17) | ~5–8 дней |
| **Итого Phase 17 block** | ~1–2 недели инкрементами |
