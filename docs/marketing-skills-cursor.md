# Marketing Skills в Cursor

Адаптация [AgentKits Marketing](https://github.com/aitytech/agentkits-marketing) (`ag_marketing/agentkits-marketing/`) для **Cursor Agent mode**.

## Что установлено

| Компонент | Путь | Количество |
|-----------|------|------------|
| Atomic marketing skills | `.cursor/skills/mkt-*/SKILL.md` | 32 |
| Workflow skills (бывшие `/commands`) | `.cursor/skills/mkt-workflow-*/SKILL.md` | 75 |
| Marketing personas | `.cursor/rules/agents/mkt-*.md` | 20 |
| Meta-skill (маршрутизация) | `.cursor/skills/using-marketing-skills/SKILL.md` | 1 |
| Brand context | `docs/marketing/brand-context.md` | — |

Исходники остаются в `ag_marketing/agentkits-marketing/` — обновляй из upstream и пересинхронизируй.

## Быстрый старт

| Задача | Claude Code | Cursor |
|--------|-------------|--------|
| План кампании | `/campaign:plan` | «Следуй skill mkt-workflow-campaign-plan» |
| SEO audit | `/seo:audit` | «Следуй skill mkt-workflow-seo-audit» |
| Landing copy | `/content:landing` | «Следуй skill mkt-workflow-content-landing» |
| CRO формы | `/cro:form` | «Следуй skill mkt-workflow-cro-form» |
| VK/ads copy | `/content:ads` | «Следуй skill mkt-workflow-content-ads» |
| 140 marketing tactics | auto / skill | `@.cursor/skills/mkt-marketing-ideas/SKILL.md` |
| Copywriter persona | agent | `@.cursor/rules/agents/mkt-copywriter.md` |

Полная карта маршрутизации: `.cursor/skills/using-marketing-skills/SKILL.md`.

## Префикс mkt-

AgentKits skills используют префикс **`mkt-`**, чтобы не конфликтовать с PM skills:

| Имя | PM (`.cursor/skills/`) | Marketing (`.cursor/skills/`) |
|-----|------------------------|-------------------------------|
| marketing-ideas | 5 идей, product marketing | **`mkt-marketing-ideas`** — 140 тактик |
| pricing-strategy | product pricing | **`mkt-pricing-strategy`** — SaaS monetization + CRO |

## Связь Marketing → PM → Engineering

```
mkt-workflow-research-market → pm-workflow-discover → idea-refine
mkt-workflow-campaign-plan   → pm-workflow-plan-launch → spec-driven-development
mkt-workflow-content-landing → frontend-ui-engineering (реализация в Next.js)
mkt-workflow-cro-form        → incremental-implementation + browser-testing
```

## Контекст chim_web

Перед marketing-задачей агент должен знать:

- `docs/marketing/brand-context.md` — продукт, аудитория, каналы
- `docs/strategy/seo-strategy.md` — SEO-стратегия
- `docs/pm/plan-3months-ads-2026-08-10.md` — план авг–окт 2026
- `frontend/app/(marketing)/` — landing pages

Артефакты: `docs/marketing/campaigns/`, `research/`, `content/`, `plans/`.

## Обновление из upstream

```bash
# 1. Обновить ag_marketing/agentkits-marketing (git pull)
# 2. Синхронизировать в Cursor
./ag_marketing/agentkits-marketing/scripts/sync-to-cursor.sh

# Dry-run
./ag_marketing/agentkits-marketing/scripts/sync-to-cursor.sh --dry-run

# Только skills + workflows (без agents)
./ag_marketing/agentkits-marketing/scripts/sync-to-cursor.sh --skip-agents
```

Скрипт:
- копирует `skills/*` → `.cursor/skills/mkt-*/` (с `references/`)
- конвертирует `commands/*/*.md` → `.cursor/skills/mkt-workflow-*/SKILL.md`
- копирует `agents/*.md` → `.cursor/rules/agents/mkt-*.md`
- **не** перезаписывает `using-marketing-skills` (ручная интеграция)
- **не** трогает PM skills без префикса

## Workflow categories

| Категория | Workflows | Примеры |
|-----------|-----------|---------|
| campaign | 4 | plan, brief, calendar, analyze |
| seo | 6 | audit, keywords, optimize, programmatic, schema, competitor |
| cro | 6 | page, form, signup, popup, onboarding, paywall |
| content | 10 | landing, blog, email, ads, social, editing, … |
| growth | 3 | launch, referral, free-tool |
| analytics | 3 | funnel, report, roi |
| research | 3 | market, persona, trend |
| sequence | 3 | welcome, nurture, re-engage |
| report | 2 | weekly, monthly |

## Рекомендации по контексту

1. **Не грузи все 107 skills сразу** — Cursor подгружает по `description`.
2. **Workflow** (`mkt-workflow-*`) — только по явному запросу.
3. **Atomic skills** — автоматически, когда релевантны (SEO, CRO, copy…).
4. **MCP-метрики** — без GA/Semrush пиши NOT AVAILABLE, не выдумывай цифры.

## Лицензия

MIT — см. `ag_marketing/agentkits-marketing/LICENSE`. Автор upstream: [AityTech / AgentKits](https://www.agentkits.net/marketing).
