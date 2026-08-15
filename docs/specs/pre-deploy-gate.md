1# Spec: Гейт деплоя + посадка reconcile

**Версия:** 0.1.0  
**Дата:** 2026-08-15  
**Статус:** черновик — ждёт ревью человека (фаза SPECIFY)  
**Источник:** [`docs/ideas/pre-deploy-gate.md`](../ideas/pre-deploy-gate.md)  
**Родитель:** [`SPEC.md`](../../SPEC.md) допущение 8 (Prod: Docker Compose на VPS); §1.8 (баллы)  
**Код баллов:** [`activity-savepoint-reconcile.md`](activity-savepoint-reconcile.md) (implemented, незакоммичен)  
**План:** TBD → `tasks/pre-deploy-gate.md` после approve  
**Аудит:** [`.cursor/workspace/audits/2026-08-15-pre-deploy-audit.md`](../../.cursor/workspace/audits/2026-08-15-pre-deploy-audit.md)

---

## Assumptions (проверьте до PLAN)

Помечены **[G#]** — поправьте сейчас, иначе после approve фиксируем как accepted.

1. **[G1]** Это **перевыкладка** уже стоящего Docker Compose (nginx → frontend → backend → Postgres + pgvector), не Kubernetes и не отдельный compose с нуля.
2. **[G2]** В SHA деплоя входит **только** `activity-savepoint-reconcile` (сервисы, роутеры stats, CLI, тесты, spec/plan/handoff, абзац SPEC §1.8 если ещё не в HEAD). Файлы `docs/ideas/gigachat-full-cutover.md`, `docs/specs/gigachat-cutover.md` и правки `docs/ideas/llm-provider-gigachat-deepseek.md` **не** коммитим в этот SHA.
3. **[G3]** Полный UoW в `get_db()` **вне scope**. Аудит-[A1] как «нет одной транзакции на запрос» не блокирует выкат. Блокирующая пользовательская дыра — сдача без баллов без самоисцеления — закрывается reconcile.
4. **[G4]** Контентные БД `test_ege.db`, `test_oge.db`, `prepared_lectures.db` лежат **в корне репозитория на хосте деплоя**. В `backend/Dockerfile` они не копируются. В базовый `docker-compose.yml` bind-mount **не** раскомментируем (сломает CI smoke, если файлов нет). Mount — через overlay `docker-compose.prod.yml`.
5. **[G5]** Публиковать Postgres на `5432` в базовом compose **не убираем** (локальный `docker compose up -d postgres` + host alembic). На VPS overlay снимает `ports`. Пароль `user`/`pass` **не ротируем** на живом volume.
6. **[G6]** `alembic upgrade head` уже в `backend/docker-entrypoint.sh` — отдельный ручной migrate на VPS не нужен, если контейнер backend стартует штатно.
7. **[G7]** Канонический origin: **`https://himych.ru`** (без `www`, без trailing slash). `NEXT_PUBLIC_API_URL` и `CORS_ORIGINS` = это значение. Frontend **запекает** URL на build — после смены URL нужна пересборка образа. Same-origin: браузер ходит на `https://himych.ru`, nginx проксирует `/api/*`.
8. **[G8]** TLS **перед** compose: сертификат на хосте / панели Timeweb / Caddy. Compose nginx остаётся HTTP (`:80` внутри, снаружи лучше `127.0.0.1:8080`). Прокси обязан слать `X-Forwarded-Proto https`. В **серверном** `.env`: `COOKIE_SECURE=true`. Ноутбучный `.env` на прод не копировать слепо.
9. **[G9]** `docker compose down -v` **запрещён** на стенде с данными. Перед `up --build` — `pg_dump`. Откат = предыдущий image tag / git SHA, том не трогать.
10. **[G10]** Сборка **без** `--no-cache`, пока нет доказательства битого слоя. CI на SHA (backend + frontend + docker-compose smoke + e2e) — гейт качества; локальный полный pytest — плюс, не замена CI, если SHA запушен.
11. **[G11]** Neuroquiz остаётся выключенным (`NEUROQUIZ_ENABLED=false`, `NEXT_PUBLIC_NEUROQUIZ_ENABLED=false`). Массовый QR-capture ответа в классе **не** входит в приёмку ([S1]/[S2] аудита).
12. **[G12]** Приёмка баллов: после сдачи ДЗ открыть статистику ученика и/или учителя — число выросло (heal-on-read допустим, отдельного баннера нет — как в spec reconcile).
13. **[G13]** Баг reconcile [Q3] (`last_active_date is None` → historical step может дернуть streak): **в том же SHA**, если воспроизводится. Не откладывать «на потом» при посадке reconcile.
14. **[G14]** Учитель на стенде уже есть (или создаётся `seed_teacher` один раз). Этот гейт не про онбординг продукта, про выкат.
15. **[G15]** Docker на VPS **ещё не установлен**. Первый прогон — на VPS после установки Docker Engine + Compose plugin, не локальный `:8080`.
16. **[G16]** `www.himych.ru` и `химыч.рф` — только 301 на `https://himych.ru`, не второй origin в CORS.

→ G1–G16: URL/SSL/VPS подтверждены 2026-08-15. Overlay-имя и абзац SPEC.md — ниже Open Questions.

---

## 1. Objective

### Что строим

Операционный **гейт выкладки** плюс посадка уже написанного reconcile в git SHA, с которого собираются образы.

Не новый продукт: учитель и ученики уже должны мочь пройти цикл на пересобранном стеке.

### Зачем

«Проверить всё и пересобрать» не является планом. Без явного SHA в прод уедет либо dirty tree, либо `main` с дырой баллов. Без mount SQLite стек живой, учебник/тесты — нет. Без дисциплины тома `down -v` уничтожит данные.

### Для кого

| Роль | Эффект |
|------|--------|
| Ops / разработчик | Повторяемый выкат: dump → overlay → build → health → цикл |
| Учитель | Кабинет, ученики, ДЗ, статистика класса (дыры баллов лечатся) |
| Ученик | Вход, учебник/тест, сдача ДЗ, баллы после stats |

### User stories + acceptance

| ID | Story | Acceptance |
|----|--------|------------|
| US-DG-1 | Как ops, выкладываю **один** git SHA | В SHA есть reconcile; нет gigachat-draft docs; working tree для деплоя чистый от этого WIP |
| US-DG-2 | Как ops, не сношу данные | `pg_dump` есть до `up`; том `chim_postgres_data` на месте; `down -v` не выполнялся |
| US-DG-3 | Как ученик, вижу учебник и тесты | Три SQLite смонтированы; лекция/вариант открываются, не 503 из‑за missing DB |
| US-DG-4 | Как пользователь, логинюсь на стенде | Cookie ставится: HTTPS + `COOKIE_SECURE=true` или HTTP + `false`; `JWT_SECRET` не дефолт `change-me-in-production` |
| US-DG-5 | Как ученик, сдаю ДЗ и вижу баллы | Submit успешен; GET своей статистики (или учитель открыл stats класса) → `total_points` / события выросли; повтор не двоит |
| US-DG-6 | Как ops, Postgres не торчит в интернет | На VPS у postgres нет опубликованного `5432` (overlay) |
| US-DG-7 | Как система, миграции применились | Backend стартовал; entrypoint прогнал `alembic upgrade head` без ошибки в логе |
| US-DG-8 | Как ops, откатываюсь без потери БД | Предыдущий SHA/образы поднимаются; том тот же |

---

## 2. Tech Stack

| Слой | Стек |
|------|------|
| Оркестрация | Docker Compose (`docker-compose.yml` + `docker-compose.prod.yml`) |
| Прокси | nginx:1.27-alpine, `nginx/nginx.conf` |
| Backend | FastAPI, Python 3.12, `backend/Dockerfile`, entrypoint alembic |
| Frontend | Next.js, `frontend/Dockerfile`, ARG `NEXT_PUBLIC_API_URL` |
| БД | `pgvector/pgvector:pg16`, volume `chim_postgres_data` |
| Контент | read-only SQLite (ЕГЭ/ОГЭ/лекции) |
| CI | GitHub Actions `.github/workflows/ci.yml` (pytest, lint, compose smoke, Playwright) |
| Баллы | существующий WIP reconcile — без новой схемы Alembic |

Новых runtime-зависимостей **не** добавляем.

---

## 3. Commands

```bash
# --- SHA (локально, после approve плана) ---
# Стекнуть / не включать gigachat docs. Коммит только по просьбе пользователя.

cd backend && .venv/bin/pytest tests/test_activity_hooks.py \
  tests/services/test_activity_reconcile.py \
  tests/test_cli_reconcile_activity.py \
  tests/test_teacher_student_stats.py -q

# Полный backend (перед пушем SHA):
cd backend && .venv/bin/pytest -q

# --- Dump до пересборки (на VPS / стенде с данными) ---
docker compose exec -T postgres pg_dump -U user chemistry > "chemistry-$(date +%Y%m%d-%H%M).sql"

# --- Prod-like up (VPS) ---
# .env на сервере: публичный URL, JWT_SECRET (свой), COOKIE_SECURE=true за HTTPS
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
# НЕ: docker compose down -v
# НЕ: --no-cache по умолчанию

docker compose ps
curl -sf "http://127.0.0.1:${NGINX_PORT:-8080}/health"
curl -sf -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:${NGINX_PORT:-8080}/"

# CLI догонка хвостов, которые никто не открывал в UI (dry-run, потом apply):
docker compose exec -T backend python -m app.cli.reconcile_activity
docker compose exec -T backend python -m app.cli.reconcile_activity --apply

# --- Локальный smoke (HTTP) ---
# В корневом .env: COOKIE_SECURE=false, NEXT_PUBLIC_API_URL=http://localhost:8080
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

CI (на запушенном SHA): push/PR в `main` → jobs `backend`, `frontend`, `docker-compose`, `e2e`. Overlay prod в CI **не** подключаем.

---

## 4. Project Structure

```
docker-compose.yml              # как сейчас; CI и локальный postgres:5432
docker-compose.prod.yml         # NEW: mount SQLite; postgres без ports
.env                            # хост деплоя, не в git
.env.example                    # плейсхолдеры + комментарий про overlay и COOKIE_SECURE
nginx/nginx.conf                # без смены в этом срезе (таймауты LLM / headers — не гейт)
backend/docker-entrypoint.sh    # alembic — не меняем
backend/app/services/activity_service.py   # уже reconcile; [G13] guard
backend/app/cli/reconcile_activity.py      # уже CLI
docs/ideas/pre-deploy-gate.md
docs/specs/pre-deploy-gate.md
tasks/pre-deploy-gate.md        # после PLAN
```

Код reconcile (уже в working tree, канон — spec activity-savepoint-reconcile):

```
backend/app/services/homework_submit_service.py
backend/app/services/test_session/{common,exam,custom,homework}_adapter.py
backend/app/api/routers/{students,teacher_stats}.py
backend/tests/...
```

---

## 5. Code Style

Overlay — минимальный diff к compose. Пример целевого `docker-compose.prod.yml`:

```yaml
# VPS / prod-like: docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
services:
  postgres:
    ports: []
  backend:
    volumes:
      - backend_data:/app/backend/data
      - ./test_ege.db:/app/test_ege.db:ro
      - ./test_oge.db:/app/test_oge.db:ro
      - ./prepared_lectures.db:/app/prepared_lectures.db:ro
```

Compose merge для `volumes` у backend **заменяет** список, поэтому `backend_data` повторяем явно.

`.env` на VPS (плейсхолдеры, не секреты):

```
NGINX_PORT=8080
NEXT_PUBLIC_API_URL=https://example.com
CORS_ORIGINS=https://example.com
JWT_SECRET=<openssl rand -hex 32, не change-me-in-production>
COOKIE_SECURE=true
NEUROQUIZ_ENABLED=false
NEXT_PUBLIC_NEUROQUIZ_ENABLED=false
```

---

## 6. Testing Strategy

| Уровень | Что | Где |
|---------|-----|-----|
| Unit / service | savepoint хука, reconcile идемпотентность, CLI dry-run, [G13] streak guard | `backend/tests/test_activity_hooks.py`, `tests/services/test_activity_reconcile.py`, `tests/test_cli_reconcile_activity.py` |
| API | teacher stats heal только своих учеников | `backend/tests/test_teacher_student_stats.py` |
| CI | ruff, mypy scoped, pytest, frontend lint/test/build, compose `/health`+`/`, Playwright login→шаг→submit ДЗ | `.github/workflows/ci.yml` |
| Ручная приёмка | US-DG-3…5: учебник/тест, логин, ДЗ, **баллы в stats** | на собранном стеке; Playwright **не** проверяет баллы — дыру гейта закрывает человек |

Новый Playwright на баллы **не** в этом срезе (Ask first, если останется время).

---

## 7. Boundaries

**Always**

- Dump БД до пересборки стенда с данными
- Деплоить конкретный git SHA, не «как в IDE»
- `JWT_SECRET` ≠ `change-me-in-production`
- Neuroquiz выключен, пока нет rate limit
- Тесты reconcile зелёные до коммита SHA
- Секреты только в `.env` хоста, не в git

**Ask first**

- `docker compose build --no-cache`
- Смена публичного URL / пересборка frontend
- Ротация `JWT_SECRET` на стенде, где уже живут сессии
- Подключать Playwright на проверку баллов
- Менять `nginx/nginx.conf` (docs, timeouts, headers)
- Пушить ветку / merge в `main`

**Never**

- `docker compose down -v` на стенде с `chim_postgres_data`
- Коммитить `.env`, ключи, дампы с ПДн
- Раскомментировать SQLite mounts в базовом `docker-compose.yml` (ломает CI)
- Тащить GigaChat cutover в этот SHA
- Переписывать все `commit()` / UoW в `get_db()`
- Включать массовый QR-ответ в приёмку без фикса [S1]
- Копировать ноутбучный `.env` поверх серверного, если не уверены, что секрет тот же

---

## 8. Success Criteria

Гейт **закрыт**, когда:

1. Существует git SHA с reconcile и без gigachat-draft; тесты из §6 (reconcile-набор) зелёные.
2. В репозитории есть `docker-compose.prod.yml` + короткий комментарий в `.env.example`.
3. На целевом стенде: dump сделан; стек поднят overlay-ем; `/health` и `/` отвечают; контентные БД читаются.
4. Ручной цикл US-DG-4 + US-DG-5 пройден (логин + сдача + баллы видны).
5. Postgres на VPS без опубликованного 5432.
6. Не выполнялся `down -v`; том на месте.

---

## 9. Not Doing

| Не делаем | Почему |
|-----------|--------|
| UoW в `get_db()` | G3; неделя call-site |
| GigaChat / смена embedding dim | draft, не гейт |
| `--no-cache` по умолчанию | G10 |
| Закрыть [S1][S2][S7][S9] | флаги / не в приёмке |
| Security headers / proxy_read_timeout nginx | не ломает цикл ученика |
| Смена пароля Postgres | G5, живой volume |
| Feature-branch CI overlay с реальными `.db` | CI остаётся API-smoke без prod mounts |

---

## 10. Open Questions

Закрыто 2026-08-15:

1. Origin: **`https://himych.ru`** ([G7]).
2. Первый прогон: **VPS**; Docker ещё не установлен ([G15]).

Ещё открыто:

3. Имя overlay: `docker-compose.prod.yml` (рекомендация спеки) или `docker-compose.content.yml`?
4. Абзац в корневом `SPEC.md` допущение 8 про overlay — или хватит `.env.example` + эта спека?

---

## 11. Риски

| Риск | Если случится | Смягчение |
|------|----------------|-----------|
| Overlay затрёт `backend_data` volume | uploads пропадут | в prod.yml явно повторить `backend_data` |
| `COOKIE_SECURE=true` на HTTP | «логин не работает» | G8; проверять схему URL |
| Frontend собран с localhost URL | API с браузера ученика уходит не туда | G7; URL до `compose build` |
| SHA без reconcile | дыра баллов как на HEAD | US-DG-1, тесты хука |
| `down -v` по привычке из CI-доки | потеря БД | Never + dump |
