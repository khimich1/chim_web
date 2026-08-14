# PM Skills в Cursor

Адаптация [PM Skills Marketplace](https://github.com/phuryn/pm-skills) (`prodakt/product-manager-agent-main/`) для **Cursor Agent mode**.

## Что установлено

| Компонент | Путь | Количество |
|-----------|------|------------|
| Atomic PM skills | `.cursor/skills/<name>/SKILL.md` | 65 |
| Workflow skills (бывшие `/commands`) | `.cursor/skills/pm-workflow-*/SKILL.md` | 36 |
| Meta-skill (маршрутизация) | `.cursor/skills/using-pm-skills/SKILL.md` | 1 |

Исходники остаются в `prodakt/product-manager-agent-main/` — их можно обновлять из upstream и пересинхронизировать.

## Быстрый старт

| Задача | В Claude Code | В Cursor |
|--------|---------------|----------|
| Discovery cycle | `/discover` | «Следуй skill pm-workflow-discover» |
| Product strategy | `/strategy` | «Следуй skill pm-workflow-strategy» |
| PRD | `/write-prd` | «Следуй skill pm-workflow-write-prd» |
| Launch / GTM | `/plan-launch` | «Следуй skill pm-workflow-plan-launch» |
| North Star | `/north-star` | «Следуй skill pm-workflow-north-star» |
| Один фреймворк (SWOT, PRD template…) | auto / skill name | «Следуй skill swot-analysis» или `@.cursor/skills/create-prd/SKILL.md` |

Полная карта маршрутизации: `.cursor/skills/using-pm-skills/SKILL.md`.

## Связь PM → Engineering

```
pm-workflow-discover → idea-refine / spec-driven-development
pm-workflow-write-prd → spec-driven-development → planning-and-task-breakdown
pm-workflow-write-stories → incremental-implementation + test-driven-development
```

Dev lifecycle: `AGENTS.md`, skill `using-agent-skills`.

## Обновление из upstream

```bash
# 1. Обновить prodakt/product-manager-agent-main (git pull / copy)
# 2. Синхронизировать в Cursor
./prodakt/product-manager-agent-main/scripts/sync-to-cursor.sh

# Dry-run
./prodakt/product-manager-agent-main/scripts/sync-to-cursor.sh --dry-run
```

Скрипт:
- копирует `pm-*/skills/*` → `.cursor/skills/<skill-name>/`
- конвертирует `pm-*/commands/*.md` → `.cursor/skills/pm-workflow-<cmd>/SKILL.md`
- **не** перезаписывает `using-pm-skills` (ручная интеграция)

## Рекомендации по контексту

1. **Не грузи все 101 skill сразу** — Cursor подгружает по `description`.
2. **Workflow** (`pm-workflow-*`) — только по явному запросу.
3. **Atomic skills** — автоматически, когда релевантны (PRD, personas, SQL…).
4. Арtefacts сохраняй в `docs/pm/` (создай каталог при первом использовании).

## Плагины

| Plugin | Workflows |
|--------|-----------|
| pm-product-discovery | discover, brainstorm, triage-requests, interview, setup-metrics |
| pm-product-strategy | strategy, business-model, value-proposition, market-scan, pricing |
| pm-execution | write-prd, plan-okrs, transform-roadmap, sprint, pre-mortem, meeting-notes, stakeholder-map, write-stories, test-scenarios, generate-data |
| pm-market-research | research-users, competitive-analysis, analyze-feedback |
| pm-data-analytics | write-query, analyze-cohorts, analyze-test |
| pm-go-to-market | plan-launch, growth-strategy, battlecard |
| pm-marketing-growth | market-product, north-star |
| pm-toolkit | review-resume, tailor-resume, draft-nda, privacy-policy, proofread |

## Лицензия

MIT — см. `prodakt/product-manager-agent-main/LICENSE`. Автор upstream: [Paweł Huryn / The Product Compass](https://www.productcompass.pm).
