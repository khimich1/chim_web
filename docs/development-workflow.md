# Правила разработки — chim_web

**Аудитория:** все разработчики проекта  
**Обновлено:** 2026-07-13  
**Связанные документы:** [Онбординг](./onboarding-developer.md) · [SPEC.md](../SPEC.md) · [tasks/plan.md](../tasks/plan.md) · `.cursor/rules/`

---

## 1. Иерархия документов

```
SPEC.md                 ← ЧТО строим, зачем, acceptance criteria, границы
    ↓
docs/specs/*.md         ← детали подсистем (tutor-rag, onboarding…)
docs/ideas/*.md         ← проработка идеи ДО попадания в SPEC
    ↓
tasks/plan.md           ← КАК реализуем: фазы, Task N, зависимости, статусы
    ↓
git (ветки, PR, коммиты) ← факт реализации
```

**Правило:** код не спорит со SPEC. Если поведение меняется — **сначала** обновить SPEC/plan, согласовать, потом код.

| Документ | Кто владеет | Когда обновлять |
|----------|-------------|-----------------|
| `SPEC.md` | владелец продукта | новая фича, смена AC, границ |
| `tasks/plan.md` | оба (sync) | новый Task, смена статуса, checkpoint |
| `docs/decisions/ADR-*.md` | инициатор решения | архитектурный выбор |
| `docs/ideas/*.md` | автор идеи | до включения в SPEC |

---

## 2. Цикл работы над фичей

```
Идея / баг / запрос
    → Есть в SPEC?  Нет → docs/ideas/ → обновить SPEC
    → Есть Task в plan?  Нет → добавить Task
    → feature-ветка
    → вертикальный срез + тесты
    → PR → ревью → merge в main
    → обновить статус Task в plan.md
```

### Четыре фазы

| Фаза | Артефакт | Когда нужна |
|------|----------|-------------|
| **Specify** | `SPEC.md` / `docs/specs/` | новая фича, изменение поведения, >30 мин работы |
| **Plan** | Task в `tasks/plan.md` | после согласования SPEC |
| **Tasks** | AC, Files, Dependencies | перед взятием в работу |
| **Implement** | код + тесты + PR | по одному Task |

**Мелкий багфикс** (1 файл, очевидный scope): Specify можно пропустить; PR должен ссылаться на AC из SPEC, если он есть.

---

## 3. Недельный ритм (для команды из 2+ человек)

### Planning (30–45 мин, раз в неделю)

1. Открыть **Progress Snapshot** в `tasks/plan.md`.
2. Выбрать **1–3 Task** на неделю.
3. Разделить владение (разные домены или зависимые Task по очереди).
4. Пометить в plan: `in progress @имя`, `queued`.
5. Сверить AC из SPEC — что значит «готово».

### Ежедневно (async)

- Утром: «беру Task N» в чате (избежать дублирования).
- Вечером: push ветки или короткий статус.

### Перед merge

- PR ревьюит **второй** разработчик.
- CI зелёный.

### Checkpoint (раз в неделю)

- Обновить статусы Task (✅ / 🟡 / блокер).
- Синхронизировать plan с фактическим кодом.

---

## 4. Алгоритм одного Task

```
1. ПРОЧИТАТЬ
   - Task N в tasks/plan.md (Description, AC, Files, Dependencies)
   - соответствующий § в SPEC.md
   - соседний код в репозитории

2. ВЕТКА
   git checkout main && git pull
   git checkout -b feature/task-101-краткое-описание

3. ВЕРТИКАЛЬНЫЙ СРЕЗ (минимальный завершённый кусок)
   Backend:  schema → repo → service → router → pytest
   Frontend: lib/api/ → component → page → vitest
   Не всё сразу — один логический шаг за коммит.

4. ПРОВЕРКА
   pytest / npm run test
   ручной smoke в браузере (если UI)
   ruff check . / npm run lint

5. КОММИТ
   feat: пресеты скорости в AudioPlayer (Task 101, SPEC §1.12.1)

6. PR
   - заголовок: Task 101: audio speed presets
   - body: ссылка на AC, что проверено
   - ревью второго разработчика

7. MERGE → обновить plan.md (✅ Task 101)
```

**Один Task = один PR** (или 2–3 маленьких PR, если Task большой — тогда дробите Task в plan).

---

## 5. Как делить работу

### По вертикальным срезам, не по слоям

| Плохо | Хорошо |
|-------|--------|
| Один — весь backend, другой — весь frontend | Каждый берёт целый Task (backend + frontend среза) |
| Оба трогают `homework_service.py` | Разные домены в одну неделю |

### Домены (стабильные границы)

| Домен | Backend | Frontend |
|-------|---------|----------|
| Textbook | `textbook_*`, `routers/textbook` | `components/textbook/` |
| Tests / Stepik | `test_session_*` | `components/tests/` |
| Homework | `homework_*`, feedback | `components/homework/` |
| Tutor / RAG | `services/tutor/`, `rag/` | `components/tutor/` |
| Teacher tools | `teacher_themes`, uploads | `components/teacher/` |
| Infra | CI, Docker, alembic | Playwright, openapi-types |

### Параллельная работа над API

1. Backend PR: schemas + router + pytest → merge.
2. Frontend может начать с mock (vitest) параллельно.
3. После merge backend — подключить `lib/api/` к реальному API.
4. CI `check:api-types` ловит drift OpenAPI ↔ TypeScript.

### Конфликты

- Разные Task → разные папки.
- Один файл нужен обоим → **очередь**: merge первого PR, rebase второго.

---

## 6. Git

### Trunk-Based Development

- `main` всегда **deployable**.
- Короткие feature-ветки: **1–3 дня**.
- Именование: `feature/краткое-описание`, `fix/...`.

### Коммиты

- **Атомарные:** одна логическая вещь на коммит.
- **Формат:** `feat:`, `fix:`, `test:`, `refactor:`, `docs:`, `chore:`.
- **Размер:** цель ~100 строк; PR >300 строк — разбить.
- **Сообщение:** объясняет **зачем**, не только что.

```
feat: пресеты скорости аудио в учебнике

Task 101, SPEC §1.12.1. Сохранение в localStorage между чанками.
```

### Не коммитить

`.env`, `*.db`, `.venv/`, `node_modules/`, `backend/uploads/`, `backend/data/rag_index.json`, `backend/data/chroma/`.

### Перед коммитом

```bash
git diff --staged
# убедиться, что нет секретов
pytest   # backend
npm run test   # frontend
```

---

## 7. Архитектурные правила кода

### Backend

- **Router → Service → Repository** — бизнес-логика не в роутерах.
- Type hints, Pydantic v2, `Depends`, `HTTPException`.
- Валидация на **границах** (HTTP body, query).
- SQLAlchemy 2.x async; параметризованные запросы, не f-string SQL.
- Секреты в `.env` через `pydantic-settings`.

### Frontend

- App Router: **Server Components** по умолчанию.
- `'use client'` только для state / events / browser APIs.
- API calls только через `frontend/lib/api/`.
- **Не** дублировать Pydantic-валидацию на клиенте.
- JWT в httpOnly cookie, `credentials: 'include'`.

### API-контракт

- Backend: Pydantic schemas + OpenAPI на `/docs`.
- Frontend: типы в `lib/api/`; drift check:

```bash
cd backend && python scripts/export_openapi.py -o openapi.json
cd frontend && npm run check:api-types
```

### Multi-teacher / безопасность

- Tenant boundary = `teacher_id`.
- Любой endpoint с ресурсом ученика/ДЗ/theme — проверка ownership.
- Регрессия: `pytest tests/multi_teacher/`.
- Не возвращать `password_hash` в response schemas.

---

## 8. Тестирование

### Пирамида

| Уровень | Инструмент | Когда |
|---------|------------|-------|
| Unit / integration | pytest (backend), vitest (frontend) | каждый срез |
| API contract | TestClient, OpenAPI drift | изменение endpoints |
| E2E | Playwright | critical flows, перед релизом |
| Browser manual | DevTools | UI-изменения, QR/voice |

### Правила

- Тесты на **реальное поведение**, не stub-assert ради coverage.
- Новый endpoint → pytest в `backend/tests/`.
- Новый UI-компонент с логикой → vitest рядом (`*.test.tsx`).
- UI merge без просмотра в браузере — red flag.

### CI (обязательно зелёный перед merge)

- ruff, mypy (scoped), pytest, coverage ≥80%
- eslint, vitest, build, openapi-types
- docker-compose smoke, Playwright e2e

---

## 9. Code Review — чеклист

Ревьюер проверяет:

1. **Scope** — PR делает одну вещь из Task?
2. **AC** — все acceptance criteria закрыты?
3. **SPEC** — нет противоречий с границами?
4. **Тесты** — pytest/vitest покрывают изменение?
5. **Безопасность** — auth/RBAC, нет секретов в diff, IDOR?
6. **Простота** — нет over-engineering и scope creep?

Approve: «AC 1–3 ок, merge».

---

## 10. Сценарии

### A: Берём существующий Task из plan

1. Task в `plan.md` → SPEC § → код.
2. Ветка → срез → тесты → PR → ✅ в plan.

### B: Новая фича

1. `docs/ideas/` (короткий one-pager).
2. Sync: входит в scope?
3. Обновить SPEC + AC.
4. Добавить Task в plan.
5. Код.

### C: Баг

1. Воспроизвести → локализовать.
2. Нарушение AC → `fix:` + тест.
3. AC не покрывал кейс → дописать AC в SPEC, потом фикс.

### D: Архитектурное решение

1. `docs/decisions/ADR-NNN-title.md`.
2. Ссылка из SPEC или plan.
3. Реализация.

---

## 11. Scope и дисциплина

- Трогай **только** то, что в Task. Соседний код — заметил → отдельная задача.
- Не смешивай форматирование с логикой в одном коммите.
- Незавершённая фича — за feature flag в settings, не долгая ветка.
- «Кажется правильно» недостаточно — нужны тесты или browser verify.

### Red flags

- Код без Task / AC
- PR >1000 строк
- Падающие тесты «починим потом»
- Секреты в git
- Endpoints без authz
- Два разработчика в одном файле без координации

---

## 12. Cursor / AI-агенты

В репозитории есть `.cursor/rules/` — workflow для AI-помощника.

| Задача | Rule |
|--------|------|
| Git, коммиты | `01-git-workflow.mdc` |
| Вертикальные срезы | `02-incremental-implementation.mdc` |
| Новая фича | `spec-driven-development.mdc` |
| API | `api-and-interface-design.mdc` |
| UI | `frontend-ui-engineering.mdc` |
| Баг | `debugging-and-error-recovery.mdc` |
| Перед merge | `code-review-and-quality.mdc` |

Справочники: `.cursor/rules/references/` (testing, security, a11y).

---

## 13. Договорённости команды (заполнить на первом sync)

| Тема | Решение |
|------|---------|
| Владелец SPEC/plan | _заполнить_ |
| Канал связи | _заполнить_ |
| Weekly planning | _день/время_ |
| SLA на review PR | _например, <24 ч_ |
| Кто деплоит | _заполнить_ |

---

## Краткая шпаргалка

**SPEC** — что готово · **plan** — какими кусками · **git/PR** — кто и когда.

Логика в backend, контент в SQLite (вне git), пользователи в PostgreSQL, фичи — вертикальными срезами с тестами.
