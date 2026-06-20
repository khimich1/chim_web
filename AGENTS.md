# AGENTS.md — Full-stack monorepo (Next.js + FastAPI)

Проект **chim_web**: monorepo с UI на Next.js и API на FastAPI. Правила в `.cursor/rules/`.

**Принцип:** бизнес-логика только в `backend/`. `frontend/` — presentation + вызовы API.

## Структура monorepo

```
chim_web/
├── backend/                    # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── models/
│   │   ├── core/
│   │   └── db/
│   ├── tests/
│   └── alembic/
├── frontend/                   # Next.js App Router
│   ├── app/                    # routes, layouts
│   ├── components/
│   ├── lib/api/                # клиент к FastAPI
│   └── package.json
└── .cursor/rules/
```

## Интеграция dev

- FastAPI: `http://localhost:8000`
- Next: `http://localhost:3000`
- `frontend/.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Backend CORS: `http://localhost:3000`
- Опционально: `rewrites` в `next.config.ts` для proxy `/api/*` → FastAPI

## Always-on rules

| Файл | Назначение |
|------|------------|
| `00-using-agent-skills.mdc` | Маршрутизация skills |
| `01-git-workflow.mdc` | Git, коммиты, размер diff |
| `02-incremental-implementation.mdc` | Вертикальные full-stack срезы |

## On-demand rules

Скажи: **«Следуй правилу `<name>`»** или включи rule в Cursor.

| Задача | Rule |
|--------|------|
| Размытая идея, нужны варианты | `idea-refine` |
| Новая фича без spec | `spec-driven-development` |
| Spec → план задач | `planning-and-task-breakdown` |
| Логика / поведение | `test-driven-development` |
| REST endpoints, контракт API | `api-and-interface-design` |
| UI, компоненты, Next.js | `frontend-ui-engineering` |
| Auth, CORS, секреты | `security-and-hardening` |
| Баг, падают тесты | `debugging-and-error-recovery` |
| Перед merge | `code-review-and-quality` |
| ADR, архитектура | `documentation-and-adrs` |
| Код по official docs | `source-driven-development` |
| Verify UI в браузере | `browser-testing-with-devtools` |

## Full-stack lifecycle

```
DEFINE  → idea-refine (опционально)       (варианты + stress-test)
          spec-driven-development        (экран + API + acceptance)
PLAN    → planning-and-task-breakdown     (backend + frontend tasks)
BUILD   → incremental-implementation
          + api-and-interface-design     (контракт первым)
          + frontend-ui-engineering      (UI)
          + test-driven-development      (pytest + vitest)
VERIFY  → browser-testing-with-devtools  (UI runtime)
REVIEW  → code-review-and-quality
SHIP    → git-workflow + documentation-and-adrs
```

## Команды

### Backend (Windows, venv)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest
pytest --cov=app
ruff check .
mypy app/
alembic upgrade head
```

### Frontend

```bash
cd frontend
npm install
npm run dev              # :3000
npm run test             # vitest
npm run test:e2e         # playwright (если настроен)
npm run lint
npm run build
```

## Персоны для ревью

`.cursor/rules/agents/` — подключай явно:

| Запрос | Файл |
|--------|------|
| Code review | `agents/code-reviewer.md` |
| Security audit | `agents/security-auditor.md` |
| Тесты / coverage | `agents/test-engineer.md` |

Пример: *«Review diff по code-reviewer и security-auditor»*.

## Справочники

| Файл | Стек |
|------|------|
| `references/testing-patterns.md` | pytest, FastAPI |
| `references/testing-patterns-frontend.md` | Vitest, RTL, MSW, Playwright |
| `references/security-checklist.md` | OWASP, pre-commit |
| `references/accessibility-checklist.md` | WCAG 2.1 AA |
| `references/idea-refine-frameworks.md` | SCAMPER, HMW, JTBD и др. |
| `references/idea-refine-criteria.md` | Rubric для фазы Evaluate |
| `docs/ideas/written-homework-photo-submit.md` | Фото рукописи в ДЗ vs compare в практике (§1.9.8) |

## Конвенции

### Backend
- Type hints, Pydantic v2, `Depends`, `HTTPException`
- Router → Service → Repository
- Секреты в `.env` + `pydantic-settings`
- Валидация на границах

### Frontend
- App Router: Server Components по умолчанию
- `'use client'` только для state/events/browser APIs
- API calls через `lib/api/` — не разбросанный `fetch`
- Не дублировать Pydantic-валидацию
- JWT не в `localStorage` — httpOnly cookies + `credentials: 'include'`

### Общее
- TDD: pytest (backend) + vitest (frontend)
- Атомарные коммиты ~100 строк
- Не коммитить без явной просьбы пользователя
- Не грузить все rules сразу

## Артефакты

| Файл | Когда |
|------|-------|
| `docs/ideas/*.md` | После idea-refine (one-pager) |
| `SPEC.md` | После spec |
| `tasks/plan.md` | После plan |
| `docs/decisions/ADR-*.md` | Архитектурные решения |

## Источник rules

Адаптировано из [agent-skills-main/](agent-skills-main/). Оригинал — reference.
