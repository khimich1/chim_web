# Cursor Platform — Composer, Grok, Skills, Subagents

Справочник для адаптации agent-skills под **Cursor IDE** (Agent / Composer, модели вроде Grok), а не Claude Code.

## Слои

| Слой | Где | Роль |
|------|-----|------|
| **Skills** | `.cursor/skills/<name>/SKILL.md` | Workflow с шагами и exit criteria |
| **Rules** | `.cursor/rules/*.mdc` | Always-on и on-demand правила проекта |
| **Personas** | `.cursor/rules/agents/*.md` | Роль + формат вывода (code-reviewer, security-auditor, test-engineer) |
| **References** | `.cursor/rules/references/` | Чеклисты и паттерны по запросу |

**Правило:** пользователь (или явный prompt) — оркестратор. Persona не вызывает другую persona. Skill — обязательный hop внутри workflow.

## Как вызывать skill

```
Следуй skill test-driven-development
@.cursor/skills/spec-driven-development/SKILL.md
```

Skills подгружаются по `description` в frontmatter. Не грузи все skills сразу — только релевантные фазе.

## Composer (Agent mode)

- Полный доступ к инструментам: Shell, Read, Write, Grep, Task, MCP
- Основной режим для BUILD / VERIFY / SHIP
- Оркестрирует subagents через **Task tool**
- Коммитит только по явной просьбе пользователя

## Grok и cross-model review

Для второго мнения (doubt-driven, code review):

1. **Task + другая модель** — `Task` с `model: cursor-grok-4.5-high` (или другой доступной модели)
2. **Новый чат** — пользователь переключает модель на Grok и вставляет ARTIFACT + CONTRACT
3. **Ручной review** — пользователь копирует артефакт во внешний инструмент

Агент **предлагает** cross-model; пользователь решает. Без явного согласия внешние CLI не запускать.

## Subagents (Task tool)

| subagent_type | Когда |
|---------------|-------|
| `explore` | Быстрый поиск по кодовой базе, API, структуре |
| `generalPurpose` | Изолированная задача (repro-тест, исследование) |
| `shell` | Git, pytest, npm, длинные команды |
| `bugbot` | Ревью diff по запросу пользователя |
| `security-review` | Security audit diff |
| `ci-investigator` | Разбор упавшего CI check |

**Ограничения Cursor:**
- Subagent **не может** запустить другой subagent → doubt-driven и orchestration только из **главной сессии**
- Параллельный fan-out: **несколько Task в одном сообщении** (code-reviewer + security-auditor + test-engineer)
- Subagent не видит историю чата пользователя — передай контекст в `prompt`

### Пример: параллельное ревью перед merge

```
Task(subagent_type=bugbot, prompt="Review branch changes по .cursor/rules/agents/code-reviewer.md …")
Task(subagent_type=security-review, prompt="Security review …")
Task(subagent_type=generalPurpose, prompt="Coverage review по .cursor/rules/agents/test-engineer.md …")
→ Синтез в главной сессии
```

### Пример: repro-тест без знания фикса

```
Task(subagent_type=generalPurpose, prompt="Напиши падающий pytest/vitest тест для бага: …")
→ Главная сессия: убедись что тест падает → фикс → тест зелёный
```

## Personas (`.cursor/rules/agents/`)

Persona — markdown с ролью и форматом ответа. В Cursor:

1. Прочитай файл persona
2. Вставь содержимое + задачу в prompt Task или выполни в текущей сессии
3. Для adversarial review (doubt-driven) — **adversarial prompt имеет приоритет** над дефолтным форматом persona

| Persona | Файл |
|---------|------|
| Code review | `.cursor/rules/agents/code-reviewer.md` |
| Security | `.cursor/rules/agents/security-auditor.md` |
| Tests / coverage | `.cursor/rules/agents/test-engineer.md` |

## MCP в Cursor

Конфиг: **Cursor Settings → MCP** или `~/.cursor/mcp.json`.

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

После изменения — перезапуск Cursor. Для browser-testing-with-devtools: `GetMcpTools` → `CallMcpTool`.

## Lifecycle без slash commands

Claude Code: `/spec`, `/plan`, `/ship`. В Cursor — явные skills:

| Фаза | Действие |
|------|----------|
| DEFINE | `idea-refine` → `spec-driven-development` |
| PLAN | `planning-and-task-breakdown` |
| BUILD | `incremental-implementation` + `test-driven-development` |
| VERIFY | `browser-testing-with-devtools`, `debugging-and-error-recovery` |
| REVIEW | `code-review-and-quality`, `security-and-hardening` |
| SHIP | `git-workflow-and-versioning`, `shipping-and-launch` |

## Документация для агентов

| Файл | Назначение |
|------|------------|
| `AGENTS.md` | Онбординг, команды, lifecycle |
| `.cursor/rules/` | Конвенции проекта |
| `SPEC.md`, `tasks/plan.md` | Spec и план |
| `docs/decisions/ADR-*.md` | Архитектурные решения |

Не используй `CLAUDE.md` — в этом проекте источник правды `AGENTS.md` + `.cursor/rules/`.

## Anti-patterns

| Anti-pattern | Вместо |
|--------------|--------|
| Persona вызывает persona | Пользователь или главная сессия запускает Task параллельно |
| Router-persona «реши кого вызвать» | `using-agent-skills` + явный запрос пользователя |
| Nested Task из subagent | Эскалация в главную сессию |
| Все skills/rules в контекст | 2–3 essential + phase-specific по задаче |
