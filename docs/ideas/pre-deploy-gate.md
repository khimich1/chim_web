# Гейт деплоя + reconcile

**Проект:** `chim_web`  
**Дата:** 2026-08-15  
**Статус:** идея согласована → spec  
**Спека:** [`docs/specs/pre-deploy-gate.md`](../specs/pre-deploy-gate.md)  
**Связано:** [`activity-savepoint-reconcile.md`](activity-savepoint-reconcile.md); аудит [`.cursor/workspace/audits/2026-08-15-pre-deploy-audit.md`](../../.cursor/workspace/audits/2026-08-15-pre-deploy-audit.md); SPEC §8 (деплой)

---

## Problem Statement

How might we на этой неделе перевыложить уже стоящий chim_web так, чтобы учитель и ученик прошли вход → учебник/тест → сдачу ДЗ → **увидели баллы** — не забирая в прод незаконченный WIP (кроме reconcile) и не снося данные стенда?

## Recommended Direction

**Гейт на один SHA + священный том Postgres + ручная приёмка учебного цикла.**

Полный UoW в `get_db()` ([A1] аудита как «нет одной транзакции на запрос») — не блокер этого выката. Пользовательская дыра — «сдано, баллов нет, 409 на повтор» — закрывается уже реализованным `activity-savepoint-reconcile` (savepoint + догонка на stats + CLI). GigaChat, neuroquiz и массовый QR в класс — не этот релиз.

`--no-cache` не обязателен: риск не кэш Docker, а `docker compose down -v` и чужой `.env`.

## Key Assumptions to Validate

- [ ] Стенд — тот же Docker Compose (nginx → Next + FastAPI + PostgreSQL), не новая оркестрация
- [ ] Контентные SQLite есть на хосте деплоя; в образ они не копируются — нужен mount
- [ ] На VPS HTTPS → `COOKIE_SECURE=true`; локальный smoke по HTTP с этим флагом не залогинит
- [ ] Менять `JWT_SECRET` на уже живом стенде нельзя, если там уже свой ключ (все сессии умрут)

## MVP Scope

- Закоммитить только reconcile (код + тесты + spec/plan). Документы GigaChat — не в SHA
- Overlay/runbook: mount трёх `.db`, не публиковать Postgres наружу, `pg_dump` до любых `up`
- `docker compose up --build -d` (без `--no-cache` по умолчанию); alembic уже в entrypoint backend
- Ручной прогон: логин → учебник или шаг теста → сдача ДЗ → баллы в статистике
- Neuroquiz выключен; массовый QR не в приёмке

## Not Doing (and Why)

- **Полный UoW в `get_db()`** — неделя чужого `commit()`, не чинит критерий успеха быстрее reconcile
- **GigaChat cutover** — draft-спека, embeddings/dim не готовы
- **`--no-cache` как ритуал** — часы ожидания, ложное чувство контроля
- **Закрыть все High аудита** ([S1] QR, [S2] neuroquiz, StepView-бог) — флаги/не включать сценарий
- **Ротация пароля Postgres на живом volume** — сломает существующий том без migrate пользователей БД

## Open Questions

- Overlay: оставить имя `docker-compose.prod.yml`? (рекомендация — да)
- Короткий абзац в `SPEC.md` допущение 8 — или хватит `.env.example` + эта идея/спека?

Закрыто: origin `https://himych.ru`; TLS перед compose; первый прогон на VPS; Docker на сервере ещё не стоит.
