# Система баллов и рейтинга

**Проект:** `chim_web`  
**Дата:** 2026-06-19  
**Статус:** идея согласована → формализация в [`SPEC.md`](../../SPEC.md) §1.8, план — Phase 13 (`tasks/plan.md`, Tasks 58–65)

---

## Problem Statement

Как мотивировать учеников регулярно решать задания и дать преподавателю прозрачную картину активности — через баллы, streak, время и глобальный рейтинг?

Сейчас в приложении есть пошаговые тесты (`TestSession`, `TestSessionStep`), сдача ДЗ (`HomeworkItemProgress`, `homework_submit_service`) и возобновление сессий (§1.3.2), но нет единой метрики прогресса и соревновательного контекста. В [`SPEC.md`](../../SPEC.md) v0.7.x рейтинги и геймификация были в «Вне scope v1»; эта идея переносит **лёгкую геймификацию** в отдельный срез после MVP core.

---

## Recommended Direction

**Ledger-first model:** append-only журнал событий `student_activity_events` + денормализованная агрегатная таблица `student_stats` для быстрых чтений (дашборд, рейтинг).

Принципы:

- События пишутся **один раз** (идемпотентность по `student_id` + `event_type` + `ref_id`).
- Баллы **не пересчитывают** `TestSession.score` — это отдельная игровая метрика, не экзаменационный балл.
- Хуки в существующие сервисы, без дублирования логики проверки ответов.

### Point rules (v1)

| Событие | Баллы | Условие |
|---------|------:|---------|
| Верный шаг | +10 | Первый раз за шаг (`step_correct`); повторная проверка того же шага — 0 |
| Сдача ДЗ | +50 | Бонус при полной сдаче `homework_complete` |
| Свободная практика | +10/шаг | Без `homework_assignment_id` — те же правила за верный шаг |
| Streak (день) | +5 | Календарный день с ≥1 верным шагом |
| Streak (7 дней) | +30 | Непрерывная серия 7 дней с активностью |

**Не начисляется:** неверные попытки, повторная проверка уже засчитанного шага, «фарм» через перезапуск сессии (идемпотентность по `ref_id` шага).

### Streak

- День считается активным, если в нём есть **≥1 верный шаг** (`step_correct`).
- Серия (`current_streak`, `longest_streak`) хранится в `student_stats`.
- Бонусы streak начисляются через события `streak_daily` / `streak_weekly` с идемпотентностью по дате/неделе.

### Time tracking

| Метрика | Источник | Примечание |
|---------|----------|------------|
| Длительность сессии | `TestSession.completed_at - created_at` | Только для `status = completed` |
| Текущая сессия | `now - created_at` | Для `in_progress` — показ «прошло N мин» в UI |
| Суммарное время | `student_stats.total_minutes` | Агрегат при `complete` сессии |

**Не в MVP:** active time по heartbeats / focus tracking.

### Leaderboard

| Вид | Период | Endpoint |
|-----|--------|----------|
| Глобальный рейтинг | `week` (default), `all_time` | `GET /api/leaderboard?period=week\|all_time&limit=50` |
| Статистика ученика | — | `GET /api/students/me/stats` |
| Статистика своих учеников (teacher) | — | `GET /api/teacher/students/stats` |

В публичном топе — **`display_name`**, не email. Преподаватель видит расширенную статистику только своих учеников (RBAC по `teacher_id`).

### Architecture hooks

Существующие точки интеграции (не переписывать flow):

```
test_session_service.check_step()     → activity_service.record_step_correct()
homework_submit_service.submit()      → activity_service.record_homework_complete()
TestSession (in_progress) + §1.3.2    → UI «Продолжить» (backend уже есть; улучшения — frontend)
```

`TestSession` / `TestSessionStep` — источник истины для верности ответа; `HomeworkItemProgress` — прогресс по пунктам ДЗ. Activity layer только **слушает** успешные события.

### New entities (app DB)

**`student_activity_events`** (append-only):

- `id`, `student_id`, `event_type`, `ref_id` (uuid/int — id шага, ДЗ и т.д.)
- `points`, `payload` (jsonb, опционально)
- `created_at`
- Уникальный индекс: `(student_id, event_type, ref_id)` — идемпотентность

**`student_stats`** (денормализация):

- `student_id` (PK)
- `total_points`, `week_points` (сброс/пересчёт по календарной неделе)
- `current_streak`, `longest_streak`, `last_active_date`
- `tasks_solved` (уникальные верные шаги)
- `total_minutes`
- `updated_at`

**`StudentProfile.display_name`:**

- Публичное имя в рейтинге; миграция на `student_profiles`.

---

## Key Assumptions to Validate

1. Ученикам интересно **глобальное** соревнование (не только внутри класса одного преподавателя).
2. **+10 за шаг** ощущается значимо, но не провоцирует фарм тривиальных заданий.
3. Порог streak (**1 верный шаг в день**) достаточен для ежедневного возврата.
4. **`display_name`** достаточен для приватности (без email в топе).

---

## MVP Scope

**IN:**

- Event ledger + `student_stats`
- Баллы за верный шаг, сдачу ДЗ, streak
- Учёт времени сессий (`total_minutes`)
- Глобальный рейтинг: `week` + `all_time`
- Виджет прогресса на дашборде ученика
- Статистика учеников для преподавателя
- UI: карточки «Продолжить» / resume (улучшения поверх §1.3.2)

**OUT:**

- Уровни, бейджи, магазин
- Настраиваемые правила баллов преподавателем
- Active time (heartbeats)
- Нормализация ЕГЭ/ОГЭ в одном рейтинге
- Push-уведомления о streak
- Продвинутый anticheat

---

## Not Doing

- Баллы за неверные попытки
- Сложная геймификация (квесты, лутбоксы)
- Email в публичном рейтинге
- Real-time WebSocket leaderboard
- Перезапись `TestSession.score` под игровые баллы

---

## Open Questions

1. **`display_name`:** задаёт ученик в профиле или маскированный email по умолчанию?
2. **Opt-out** из глобального рейтинга (скрыть из топа, но оставить личную статистику)?
3. **Бонус за ДЗ:** фиксированные +50 или % от `score/max_score`?
4. **Когда** включить в формальный SPEC (сейчас — §1.8 черновик; полный US/AC — после пилота на 2–3 учениках)?

---

## Codebase anchors

| Сущность / модуль | Роль |
|-------------------|------|
| `TestSession`, `TestSessionStep` | Пошаговые тесты; `check_step` → источник `step_correct` |
| `HomeworkItemProgress` | Per-item прогресс ДЗ |
| `homework_submit_service` | Полная сдача ДЗ → `homework_complete` |
| `test_session_service.check_step()` | Хук начисления за верный шаг |
| `StudentProfile` | Расширить `display_name` |
| SPEC «Вне scope v1» | Ранее: «Рейтинги, геймификация» — перенесено в §1.8 |

---

## Ссылки

- [`SPEC.md`](../../SPEC.md) §1.8 — формальное описание фичи
- [`tasks/plan.md`](../../tasks/plan.md) — Phase 13, Tasks 58–65
