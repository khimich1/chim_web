# Целостность сдачи и баллов (savepoint + reconcile)

**Проект:** `chim_web`  
**Дата:** 2026-08-15  
**Статус:** идея согласована → spec + plan approved → IMPLEMENT  
**Спека:** [`docs/specs/activity-savepoint-reconcile.md`](../specs/activity-savepoint-reconcile.md)  
**План:** [`tasks/activity-savepoint-reconcile.md`](../../tasks/activity-savepoint-reconcile.md)  
**Handoff:** [`docs/handoffs/activity-savepoint-reconcile.md`](../handoffs/activity-savepoint-reconcile.md)  
**Связано:** аудит [A1] (размытое владение транзакцией); SPEC §1.8; [`student-points-leaderboard.md`](student-points-leaderboard.md); [`partial-homework-submit.md`](partial-homework-submit.md); выкат: [`pre-deploy-gate.md`](pre-deploy-gate.md)

---

## Problem Statement

Как сделать так, чтобы сдача ДЗ и шаг теста для ученика либо сохранялись целиком, либо ученик мог повторить — и при этом редкий сбой начисления баллов не откатывал работу и не оставлял вечную дыру в рейтинге, **без** переписывания всех `commit()` до деплоя?

## Recommended Direction

**Savepoint на баллы + догонка при чтении + разовый CLI backfill.** Сдача/шаг — обязательный факт одной транзакции. Баллы — вложенный savepoint: ошибка не трогает основное. Ledger — проекция: её дописывают `GET /stats`, статистика учителя и CLI по `HOMEWORK_COMPLETE` / `STEP_CORRECT`. Полный UoW в `get_db()` — не этот срез.

Это совпадает с ledger-first моделью §1.8 (хуки слушают домен, события идемпотентны) и чинит баг хука: второй `commit` + `rollback` той же сессии.

## Key Assumptions to Validate

- [ ] Потерянные `HOMEWORK_COMPLETE` / `STEP_CORRECT` однозначно выводятся из доменных таблиц (инжект «сдача есть, события нет» → stats чинит ровно один раз; CLI на той же фикстуре)
- [ ] Backfill с исходным `occurred_at` не двигает streak «на сегодня»
- [ ] Задержка баллов до просмотра статистики приемлема — **не валидируем заранее**, смотрим по тикетам после выкладки

## MVP Scope

- Убрать `commit`/`rollback` из activity-хуков; один внешний `commit` в конце `submit` и `check_step`
- Баллы в `begin_nested()`; ошибка — лог, сдача живёт
- Reconcile в `get_stats` и в статистике учителя: только два типа событий
- CLI разового backfill тех же двух типов — **в том же PR**
- Тесты: хук падает → ДЗ/шаг в БД; повторный stats и повторный CLI не двоят баллы

## Not Doing (and Why)

- **Строгая атомарность (нет баллов → нет сдачи)** — сознательно best-effort баллы, чтобы не терять работу ученика
- **Savepoint без догонки** — легализует вечный рассинхрон рейтинга
- **Полный UoW в `get_db()` до деплоя** — неделя чужого кода ради двух путей
- **Догонка `HOMEWORK_COMPLETE_DELTA` и streak-событий в v1** — легко сломать идемпотентность и календарь
- **Reconcile на GET homework / GET leaderboard (полный скан)** — скрывает баги write-пути; лидерборд не должен лечить всех учеников на каждый запрос
- **Заранее выбранный план «если будут тикеты»** — решим по факту после выкладки

## Open Questions

- Если после выкладки тикеты «нет баллов» — атомарность, расширение догонки или CLI как операционка?
