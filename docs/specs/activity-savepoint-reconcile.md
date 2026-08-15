# Spec: Целостность сдачи ДЗ / шага теста и баллов (savepoint + reconcile)

**Версия:** 0.1.0  
**Дата:** 2026-08-15  
**Статус:** implemented 2026-08-15  
**Источник:** [`docs/ideas/activity-savepoint-reconcile.md`](../ideas/activity-savepoint-reconcile.md)  
**Родитель:** SPEC.md §1.8, [`docs/ideas/student-points-leaderboard.md`](../ideas/student-points-leaderboard.md)  
**План:** [`tasks/activity-savepoint-reconcile.md`](../../tasks/activity-savepoint-reconcile.md)  
**Handoff:** [`docs/handoffs/activity-savepoint-reconcile.md`](../handoffs/activity-savepoint-reconcile.md)

---

## Assumptions (accepted 2026-08-15)

Помечены **[A#]** — поправь до approve, иначе фиксируем как accepted.

1. **[A1]** Отдельная спека `docs/specs/activity-savepoint-reconcile.md`. Канон баллов остаётся SPEC §1.8; после approve в §1.8 добавляется короткий абзац «хуки не коммитят; догонка двух типов событий» — не переписываем правила очков.
2. **[A2]** Срез **хирургический:** только `HomeworkSubmitService.submit` и `check_step` в exam/custom/homework адаптерах (+ общий `run_activity_hook`). Tutor, uploads, students, neuroquiz, onboarding `commit()` **не трогаем**.
3. **[A3]** Политика: сдача/шаг обязательны, баллы best-effort (savepoint). Строгая атомарность («нет баллов → нет сдачи») **не** в этом срезе.
4. **[A4]** Догонка на чтении: `GET /api/students/me/stats` (этот ученик) и `GET /api/teacher/students/stats` (каждый ученик в ответе). **`GET /api/leaderboard` не сканирует и не лечит всех** — иначе N записей на каждый просмотр рейтинга. Глобальный хвост закрывает CLI.
5. **[A5]** Восстанавливаем только `HOMEWORK_COMPLETE` и `STEP_CORRECT`. Не трогаем `HOMEWORK_COMPLETE_DELTA`, `STREAK_*`, onboarding-события, `total_minutes`.
6. **[A6]** CLI в том же PR: `python -m app.cli.reconcile_activity`. По умолчанию dry-run; запись только с `--apply`.
7. **[A7]** `occurred_at` при догонке: `HomeworkSubmission.submitted_at` и `TestSessionStep.checked_at`. Не `now()` — иначе streak «переезжает» на сегодня.
8. **[A8]** Миграций Alembic нет. Схема ledger/stats не меняется.
9. **[A9]** Frontend не меняется. Задержка баллов до просмотра статистики — допустимый UX этого среза; отдельного баннера нет.
10. **[A10]** Уведомление учителю остаётся в **той же** внешней транзакции, что статус `SUBMITTED` (как сейчас до activity-хука). Падение баллов не должно откатывать уведомление.
11. **[A11]** Промежуточные `commit()` в адаптерах на *других* методах (attach image, complete session, reopen) вне `check_step`/`submit` — не в scope, даже если это тоже «владение транзакцией».
12. **[A12]** SQLite в pytest: `begin_nested()` (SAVEPOINT) уже используется в `ActivityRepository.try_create_event`; новый savepoint вокруг хука должен работать на той же тестовой БД.
13. **[A13]** Если `HOMEWORK_COMPLETE` отсутствует полностью — создаём одно событие с баллами `compute_homework_points(answered_steps, total_steps)` текущего submission. Не восстанавливаем цепочку delta. Если `HOMEWORK_COMPLETE` уже есть, а delta нет — **не** чиним (известная дыра v1).
14. **[A14]** Догонка на GET stats — осознанный side-effect на чтении: после heal нужен `commit` на этих двух endpoints (сейчас `get_my_stats` не коммитит).
15. **[A15]** Запасной план при тикетах «нет баллов» **не кодируем** в этом срезе (атомарность vs delta/streak vs операционка — после выкладки).

→ A1–A15 accepted 2026-08-15. C1–C3 (нет homework check_step; complete_session commit после хука; streak/week guard) — accepted.

---

## 1. Objective

### Что строим

Исправление критического бага аудита **[A1]** на двух пользовательских путях:

1. **Write path.** Сдача ДЗ и проверка шага теста коммитятся один раз. Начисление баллов идёт во вложенном savepoint: ошибка activity **не** делает `rollback` сессии, где уже лежит работа ученика.
2. **Read/ops path.** Проекция ledger догоняется: при просмотре статистики ученика/учителя и разовым CLI. Только два типа событий.

### Зачем

Сейчас `_run_activity_hook` / `run_activity_hook` делают второй `commit`, а при исключении — `rollback` той же `AsyncSession`. После `commit` сдачи это оставляет «сдано без баллов»; если промежуточный `commit` когда-нибудь уберут, `rollback` сотрёт и сдачу. В проде это порча доменных данных без самоисцеления (`409` на повторный submit).

### Для кого

| Роль | Эффект |
|------|--------|
| Ученик | Работа (ДЗ / зачтённый шаг) не пропадает из‑за сбоя баллов |
| Учитель | Видит сдачу; баллы ученика подтягиваются при открытии статистики класса |
| Ops | Dry-run + `--apply` закрывают хвосты, которые никто не открывал в UI |
| Разработчик | Хуки больше не владеют транзакцией; тесты фиксируют инвариант |

### User stories + acceptance

| ID | Story | Acceptance |
|----|--------|------------|
| US-AS-1 | Как ученик, сдаю ДЗ; activity падает | HTTP не 5xx из‑за хука; assignment `SUBMITTED`; submission и уведомление в БД; баллов может не быть до stats/CLI |
| US-AS-2 | Как ученик, проверяю шаг; activity падает | Шаг `CHECKED`, `is_correct` сохранён; сессия не откатилась |
| US-AS-3 | Как ученик, открываю свою статистику при дыре | Появляется ровно одно недостающее `HOMEWORK_COMPLETE` и/или `STEP_CORRECT`; повторный GET не двоит |
| US-AS-4 | Как учитель, открываю статистику класса | Те же дыры у своих учеников закрываются в этом запросе |
| US-AS-5 | Как ops, гоняю CLI без `--apply` | Печать что было бы создано; БД не меняется |
| US-AS-6 | Как ops, гоняю CLI `--apply` | Создаются только недостающие два типа; повторный прогон — 0 новых |
| US-AS-7 | Как ученик, сдаю ДЗ в счастливом пути | Баллы начисляются в том же запросе, как сейчас (не «только через stats») |

---

## 2. Tech Stack

| Слой | Стек |
|------|------|
| Backend | FastAPI, SQLAlchemy 2.x async (`AsyncSession.begin_nested`) |
| Ledger | `StudentActivityEvent` UNIQUE `(student_id, event_type, ref_id)` |
| Stats | `StudentStats` (денормализация через `ActivityService.record_*`) |
| CLI | `python -m app.cli.reconcile_activity` (как `seed_teacher`) |
| Tests | pytest + sqlite aiosqlite; без новой схемы |
| Frontend | без изменений |

---

## 3. Commands

```bash
cd backend

# Регрессия хуков и баллов
pytest tests/test_activity_hooks.py tests/test_activity_service.py \
  tests/test_homework_partial_submit.py tests/services/test_homework_services_unit.py -q

# После добавления тестов среза
pytest tests/services/test_activity_reconcile.py tests/test_cli_reconcile_activity.py -q

# Полный backend
pytest -q

# CLI (staging/prod): сначала смотрим
python -m app.cli.reconcile_activity
python -m app.cli.reconcile_activity --student-id <uuid>
# запись
python -m app.cli.reconcile_activity --apply
```

Lint/type по репозиторию: `ruff check .` из `backend/`, при наличии `mypy app/`.

---

## 4. Project Structure

```
backend/app/db/session.py                         → не меняем get_db() в этом срезе
backend/app/services/homework_submit_service.py   → submit: один commit; хук = savepoint
backend/app/services/test_session/common.py       → run_activity_hook без commit/rollback
backend/app/services/test_session/exam_adapter.py
backend/app/services/test_session/custom_adapter.py
backend/app/services/test_session/homework_adapter.py  → check_step: commit после savepoint
backend/app/services/activity_service.py          → reconcile_student(); occurred_at на backfill
backend/app/api/routers/students.py               → GET me/stats: reconcile + commit
backend/app/api/routers/teacher_stats.py          → list stats: reconcile listed + commit
backend/app/cli/reconcile_activity.py             → новый CLI
backend/tests/services/test_activity_reconcile.py → unit догонки
backend/tests/test_cli_reconcile_activity.py      → dry-run / --apply
backend/tests/test_activity_hooks.py              → hook failure не стирает домен
docs/ideas/activity-savepoint-reconcile.md
docs/specs/activity-savepoint-reconcile.md
```

---

## 5. Code Style

Общий хук — **без** `commit`/`rollback` сессии. Savepoint откатывает только баллы:

```python
async def run_activity_hook(
    self,
    hook_name: str,
    action: Callable[[], Awaitable[_T]],
) -> None:
    try:
        async with self._session.begin_nested():
            await action()
    except Exception:
        logger.exception("Activity hook failed: %s", hook_name)
```

`check_step` / `submit`: мутации домена, затем хук, затем **один** `await self._session.commit()`.

Догонка (сервис, не роутер):

```python
async def reconcile_student(self, student_id: uuid.UUID) -> int:
    """Insert missing HOMEWORK_COMPLETE / STEP_CORRECT. Idempotent. Returns rows created."""
    created = 0
    created += await self._reconcile_homework_complete(student_id)
    created += await self._reconcile_step_correct(student_id)
    return created
```

- `record_homework_complete(..., occurred_at=submission.submitted_at, points=compute_homework_points(...))`
- `record_step_correct(..., occurred_at=step.checked_at)` — только шаги с `is_correct is True`
- Роутеры stats после reconcile: `await db.commit()` (A14)
- Именование: `reconcile_*`, не `fix_*` / `repair_*`
- Лог хука: имя хука + exception; **не** PII ученика

---

## 6. Testing Strategy

| Уровень | Где | Что доказывает |
|---------|-----|----------------|
| Unit | `tests/services/test_activity_reconcile.py` | Дыра → одно событие; повтор → 0; `occurred_at` со шага/submission; delta не создаётся |
| Unit / service | существующие homework unit | счастливый submit по-прежнему пишет баллы до возврата |
| Integration | `tests/test_activity_hooks.py` | **Prove-it:** хук бросает → ДЗ/шаг в БД, статус не откатился |
| CLI | `tests/test_cli_reconcile_activity.py` | dry-run 0 writes; `--apply` идемпотентен |
| Регрессия | `test_homework_partial_submit.py`, `test_activity_service.py` | частичная сдача и streak на **живом** хуке не сломаны |

Не требуем новый E2E Playwright. Coverage: новые ветки хука (успех / exception) и reconcile (пусто / дыра / уже есть).

Prove-it (обязательный падающий тест до фикса):

```python
async def test_homework_submit_keeps_assignment_when_activity_raises(...):
    # activity.record_homework_complete raises
    # POST submit → 200, assignment SUBMITTED, no HOMEWORK_COMPLETE row
```

---

## 7. Boundaries

**Always**

- Тесты из §3 зелёные до коммита
- Хуки activity не вызывают `session.commit()` / `session.rollback()`
- Догонка идемпотентна через существующий UNIQUE
- CLI по умолчанию dry-run
- `occurred_at` с доменных timestamps

**Ask first**

- Расширение догонки на `HOMEWORK_COMPLETE_DELTA` / streak
- Перенос `commit` в `get_db()` (полный UoW)
- Reconcile внутри `GET /api/leaderboard`
- Новые зависимости, Alembic, смена правил очков §1.8
- Строгая атомарность вместо savepoint

**Never**

- `rollback()` внешней сессии из activity-хука
- Backfill streak/`delta` «датой запуска CLI»
- Секреты в CLI-выводе
- Удалять/скипать падающие тесты хуков без явного одобрения
- Менять frontend «чтобы скрыть задержку баллов»

---

## 8. Success Criteria

Срез готов, когда все пункты истинны:

1. `run_activity_hook` / `_run_activity_hook` не содержат `commit`/`rollback`.
2. `submit` и три `check_step` делают один внешний `commit` после хука.
3. Тест «activity raises → домен сохранён» зелёный (US-AS-1, US-AS-2).
4. Счастливый путь по-прежнему начисляет баллы в том же запросе (US-AS-7).
5. `reconcile_student` закрывает только два типа событий и идемпотентен (US-AS-3).
6. Teacher stats вызывает reconcile на перечисленных учениках и коммитит (US-AS-4).
7. CLI dry-run / `--apply` / повторный `--apply` соответствуют US-AS-5/6.
8. Нет миграций, нет изменений frontend, нет правок посторонних `commit()` (A2, A8, A9).
9. `pytest` по командам §3 зелёный.

---

## 9. Behaviour notes (write path)

Текущий антипаттерн:

```
mutate homework/step
commit()          # транзакция 1
activity hook
  commit()        # транзакция 2
  except: rollback()  # опасно для незакоммиченного; бесполезно для уже закоммиченного
```

Целевое:

```
mutate homework/step
begin_nested:
    record_* activity   # ошибка → откат savepoint, домен жив
commit()                # один раз: домен + баллы (если savepoint успел)
```

`GET /api/leaderboard` может показывать устаревшие баллы, пока не сработают stats или CLI. Это принятый лаг (A4), не баг среза.

---

## 10. Open Questions

- **[Q1]** Если после выкладки тикеты «сдано, баллов нет» — переключаемся на строгую атомарность, расширяем догонку (delta/streak) или оставляем CLI операционкой? *(решаем после выкладки, A15)*
- **[Q2]** Нужен ли `--student-id` в CLI v1 или достаточно глобального прогона? *(в спеке заложено оба; можно выкинуть фильтр, если лишний)*

---

## 11. Out of scope (явный список)

- Unit of Work на весь FastAPI (`get_db` auto-commit)
- HTTPException → доменные исключения [A2 аудита]
- QR-capture auth [S1], neuroquiz rate limit [S2]
- Догонка delta/streak/onboarding/minutes
- UI задержки баллов
- Исправление исторических неверных `points` у уже существующих событий (только *отсутствующие* строки)

---

## Changelog

- 0.1.0 — 2026-08-15: IMPLEMENT AS-1…AS-7 (savepoint хуки, reconcile_student, stats GET, CLI).
- 0.1.0-draft — 2026-08-15: первый драфт по согласованной идее 2+4 (savepoint + reconcile + CLI в том же PR).
