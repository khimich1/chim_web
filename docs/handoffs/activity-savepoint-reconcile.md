# Handoff: savepoint activity + reconcile — сразу IMPLEMENT

**Для:** новое окно Cursor Agent (Multitask)  
**Дата:** 2026-08-15  
**Статус входа:** idea ✅ → spec ✅ → plan ✅ (человек: «все устраивает») → **IMPLEMENT с AS-1 (TDD RED)**  
**Код по этой фиче ещё не писали.** Коммиты — только по явной просьбе.

Не пересобирать idea/spec/plan. Не переспрашивать три развилки ниже — они закрыты.

---

## Стартовый промпт (вставь в новое окно)

```
Следуй skills: incremental-implementation → test-driven-development.
Не делай idea-refine / spec / plan заново.

Контекст: @docs/handoffs/activity-savepoint-reconcile.md
План (канон задач): @tasks/activity-savepoint-reconcile.md
Spec: @docs/specs/activity-savepoint-reconcile.md
Idea: @docs/ideas/activity-savepoint-reconcile.md

Сразу IMPLEMENT, начиная с AS-1 (только RED-тесты, production-код не трогать).
Потом AS-2 GREEN → Checkpoint A → AS-3…AS-8 по плану.
Один срез за раз: тест → код → pytest задачи → следующий.
Не коммить без явной просьбы.
Не полный UoW в get_db, не frontend, не Alembic, не leaderboard heal, не delta/streak backfill.
Отвечай по-русски.
```

---

## Цель (одна фраза)

Сдача ДЗ и `check_step` не должны теряться из‑за сбоя начисления баллов; баллы — savepoint + догонка двух типов событий на stats и CLI.

---

## Источник правды (читать в этом порядке)

| Артефакт | Путь |
|----------|------|
| Этот handoff | `docs/handoffs/activity-savepoint-reconcile.md` |
| План задач AS-1…AS-8 | `tasks/activity-savepoint-reconcile.md` |
| Spec | `docs/specs/activity-savepoint-reconcile.md` |
| Idea | `docs/ideas/activity-savepoint-reconcile.md` |
| Баллы (не переписывать правила) | `SPEC.md` §1.8 |

Аудит-баг: [A1] размытое владение транзакцией — `.cursor/workspace/audits/2026-08-14-full-project-audit.md`.

---

## Закрытые развилки (не переоткрывать)

Человек 2026-08-15: «все устраивает» по трём конфликтам план vs spec.

| # | Решение |
|---|---------|
| C1 | У `HomeworkSessionAdapter` **нет** `check_step`. Правим только `exam_adapter.check_step` и `custom_adapter.check_step`. Homework-сессии идут через facade. |
| C2 | **Один** `run_activity_hook` без `commit`/`rollback`. В трёх `complete_session` (exam / custom / homework) переставить существующий `commit()` **после** хука `add_session_minutes`. Не плодить второй helper. |
| C3 | Исторический reconcile: если `event_date < stats.last_active_date` — только ledger + `total_points` (+ `tasks_solved` для шага). **Не** звать `_update_streak_for_new_active_day`, **не** сбрасывать `week_points`. Живой хук в том же запросе, что check_step — полный `record_*`. |

A1–A15 спеки приняты. Spec status в файле может ещё быть `draft` — не блокирует implement; статус/абзац §1.8 — задача AS-7.

---

## Что строить

**Write path:** мутации домена → `begin_nested()` для activity → один `session.commit()`. Ошибка баллов откатывает только savepoint.

**Read/ops path:** `ActivityService.reconcile_student` закрывает только отсутствующие `HOMEWORK_COMPLETE` и `STEP_CORRECT`. Вызов: `GET /api/students/me/stats`, `GET /api/teacher/students/stats` (+ `db.commit()`), CLI `python -m app.cli.reconcile_activity` (dry-run по умолчанию, `--apply`, `--student-id`).

**Leaderboard не лечит.** Frontend / Alembic / `get_db()` UoW — нет.

---

## Порядок срезов (из плана — не менять)

1. **AS-1 RED** — только тесты: хук не зовёт `commit`/`rollback`; submit/check_step сохраняют домен при raise activity. Production-код **не** менять. Доказать RED.
2. **AS-2 GREEN** — savepoint в обоих хуках; один commit после хука в `submit` + exam/custom `check_step`; перестановка commit в трёх `complete_session`.
3. Checkpoint A
4. **AS-3** — TDD `reconcile_student` + streak/week guard
5. **AS-4** ∥ **AS-5** — student stats / teacher stats heal + commit
6. Checkpoint B
7. **AS-6** CLI → **AS-7** docs → **AS-8** `pytest -q`

Вертикальный минимум для демо: AS-1+AS-2+AS-3+AS-4. CLI в том же PR (AS-6), не отдельный релиз.

Детали acceptance / files / verify — только в `tasks/activity-savepoint-reconcile.md`. Не дублировать задачи здесь.

---

## Ключевые файлы сейчас (HEAD)

**Хуки (баг):**
- `backend/app/services/test_session/common.py` — `run_activity_hook`: `commit` + `rollback`
- `backend/app/services/homework_submit_service.py` — `_run_activity_hook` то же; `submit` коммитит **до** хука

**check_step (commit до хука):**
- `backend/app/services/test_session/exam_adapter.py`
- `backend/app/services/test_session/custom_adapter.py`
- `backend/app/services/test_session/facade.py` — маршрутизация check_step (не homework adapter)

**complete_session (commit до хука минут) — C2:**
- exam / custom / `homework_adapter.py`

**Догонка:**
- `backend/app/services/activity_service.py` — `record_step_correct`, `_apply_points_to_stats`, `_update_streak_for_new_active_day`
- `backend/app/api/routers/students.py` — `GET /me/stats` без commit
- `backend/app/api/routers/teacher_stats.py`
- CLI-образец: `backend/app/cli/seed_teacher.py`

**Тесты:**
- `backend/tests/test_activity_hooks.py` — расширять в AS-1
- `backend/tests/test_homework_partial_submit.py`, `tests/services/test_homework_services_unit.py`
- `backend/tests/test_activity_service.py`
- Новый: `tests/services/test_activity_reconcile.py`, `tests/test_cli_reconcile_activity.py`

---

## Команды проверки (по фазам плана)

```bash
cd backend

# AS-1 / AS-2
pytest tests/test_activity_hooks.py tests/test_homework_partial_submit.py \
  tests/services/test_homework_services_unit.py -q

# AS-3…AS-5
pytest tests/services/test_activity_reconcile.py tests/test_activity_service.py \
  tests/test_leaderboard_api.py tests/test_teacher_student_stats.py -q

# AS-6
pytest tests/test_cli_reconcile_activity.py -q

# AS-8
pytest -q
```

Не коммитить без просьбы. `ruff` — на файлах среза, см. план «Команды проверки».

---

## Skills / rules

- Build: `.cursor/skills/incremental-implementation/SKILL.md`
- Tests: `.cursor/skills/test-driven-development/SKILL.md` (Prove-it: RED до фикса)
- Always-on: git workflow; **не коммитить без просьбы**
- Не грузить idea-refine / spec-driven заново

---

## Риски (уже с митигацией в плане)

- Смена общего хука без перестановки `complete_session.commit` → пропадут `total_minutes` (C2 закрыт)
- Слепой `record_step_correct(occurred_at=старый)` → rewind streak/week (C3 закрыт)
- Два `begin_nested` (хук + `try_create_event`) на SQLite — покрыть happy-path AS-2
- GET stats с side-effect commit — только два endpoint, не leaderboard

---

## Чего не делать в новом окне

- Не начинать с PLAN/spec/idea-refine
- Не писать AS-2, пока AS-1 unit «хук не commit/rollback» не **красный** на HEAD
- Не трогать `get_db()`, frontend, Alembic, tutor/uploads/neuroquiz commits, attach/reopen/create
- Не heal `GET /api/leaderboard`
- Не backfill `HOMEWORK_COMPLETE_DELTA` / `STREAK_*`
- Не коммитить, пока пользователь не попросит
- Не force-push / не amend чужих коммитов
