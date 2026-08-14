---
name: using-pm-skills
description: Обнаруживает и применяет PM skills (Product Manager Agent). Используй при product discovery, strategy, PRD, GTM, market research, analytics и других PM-задачах вне инженерного lifecycle.
---

# Использование PM Skills (Cursor)

## Обзор

**PM Skills Marketplace** ([phuryn/pm-skills](https://github.com/phuryn/pm-skills)) — 65 фреймворков и 36 chained workflows для product management. В Cursor адаптированы как skills в `.cursor/skills/`.

| Тип | Префикс / паттерн | Пример |
|-----|-------------------|--------|
| **Atomic skill** | kebab-case | `create-prd`, `swot-analysis`, `north-star-metric` |
| **Workflow** (бывшие `/commands`) | `pm-workflow-*` | `pm-workflow-discover`, `pm-workflow-write-prd` |

Slash commands Claude Code (`/discover`, `/strategy`) → **«Следуй skill pm-workflow-discover»** или `@.cursor/skills/pm-workflow-discover/SKILL.md`.

## Маршрутизация

```
PM-задача
    │
    ├── Новая идея / discovery? ────────→ pm-workflow-discover
    │   ├── Быстрый brainstorm ─────────→ pm-workflow-brainstorm
    │   ├── Feature requests ───────────→ pm-workflow-triage-requests
    │   ├── Customer interview ─────────→ pm-workflow-interview
    │   └── Metrics dashboard ──────────→ pm-workflow-setup-metrics
    │
    ├── Стратегия / business model? ────→ pm-workflow-strategy
    │   ├── Lean/BMC/startup canvas ────→ pm-workflow-business-model
    │   ├── Value proposition ──────────→ pm-workflow-value-proposition
    │   ├── Macro scan (SWOT/PESTLE…) ──→ pm-workflow-market-scan
    │   └── Pricing ────────────────────→ pm-workflow-pricing
    │
    ├── Execution (PRD, OKR, sprint)? ──→ pm-workflow-write-prd
    │   ├── OKRs ───────────────────────→ pm-workflow-plan-okrs
    │   ├── Outcome roadmap ────────────→ pm-workflow-transform-roadmap
    │   ├── Sprint plan/retro/release ──→ pm-workflow-sprint
    │   ├── Pre-mortem ─────────────────→ pm-workflow-pre-mortem
    │   ├── Meeting notes ──────────────→ pm-workflow-meeting-notes
    │   ├── Stakeholder map ────────────→ pm-workflow-stakeholder-map
    │   ├── User/job/WWA stories ───────→ pm-workflow-write-stories
    │   ├── Test scenarios ─────────────→ pm-workflow-test-scenarios
    │   └── Dummy dataset ──────────────→ pm-workflow-generate-data
    │
    ├── Market research? ───────────────→ pm-workflow-research-users
    │   ├── Competitive landscape ──────→ pm-workflow-competitive-analysis
    │   └── Feedback sentiment ───────→ pm-workflow-analyze-feedback
    │
    ├── Data analytics? ────────────────→ pm-workflow-write-query
    │   ├── Cohort analysis ────────────→ pm-workflow-analyze-cohorts
    │   └── A/B test ───────────────────→ pm-workflow-analyze-test
    │
    ├── Go-to-market / launch? ───────→ pm-workflow-plan-launch
    │   ├── Growth loops / motions ─────→ pm-workflow-growth-strategy
    │   └── Battlecard ─────────────────→ pm-workflow-battlecard
    │
    ├── Marketing / positioning? ───────→ pm-workflow-market-product
    │   └── North Star metric ──────────→ pm-workflow-north-star
    │
    └── PM toolkit (resume, legal)? ────→ pm-workflow-review-resume
        ├── Tailor resume ──────────────→ pm-workflow-tailor-resume
        ├── NDA / privacy ──────────────→ pm-workflow-draft-nda, pm-workflow-privacy-policy
        └── Proofread ──────────────────→ pm-workflow-proofread
```

## Связь с инженерным lifecycle

PM skills дополняют, не заменяют dev skills из `using-agent-skills`:

| PM артефакт | Следующий dev skill |
|-------------|---------------------|
| PRD (`pm-workflow-write-prd`) | `spec-driven-development` |
| Discovery plan | `idea-refine` → `spec-driven-development` |
| User stories | `planning-and-task-breakdown` → `incremental-implementation` |
| Test scenarios | `test-driven-development` |
| North Star / metrics | `spec-driven-development` (acceptance criteria) |

## Как вызывать

```
Следуй skill pm-workflow-discover для AI writing assistant
@.cursor/skills/create-prd/SKILL.md
Какие riskiest assumptions для нашей идеи?  → atomic skill identify-assumptions-new
```

**Workflow skills** (`pm-workflow-*`) — только по явному запросу (`disable-model-invocation: true`).

**Atomic skills** — подгружаются по description, когда релевантны (PRD, SWOT, personas и т.д.).

## Плагины → skills

| Plugin | Atomic skills | Workflows |
|--------|---------------|-----------|
| pm-product-discovery | 13 | discover, brainstorm, triage-requests, interview, setup-metrics |
| pm-product-strategy | 12 | strategy, business-model, value-proposition, market-scan, pricing |
| pm-execution | 15 | write-prd, plan-okrs, transform-roadmap, sprint, pre-mortem, meeting-notes, stakeholder-map, write-stories, test-scenarios, generate-data |
| pm-market-research | 7 | research-users, competitive-analysis, analyze-feedback |
| pm-data-analytics | 3 | write-query, analyze-cohorts, analyze-test |
| pm-go-to-market | 6 | plan-launch, growth-strategy, battlecard |
| pm-marketing-growth | 5 | market-product, north-star |
| pm-toolkit | 4 | review-resume, tailor-resume, draft-nda, privacy-policy, proofread |

Полный список: `ls .cursor/skills/ | grep -E '^(pm-workflow-|brainstorm|create-prd)'` или см. [docs/pm-skills-cursor.md](../../docs/pm-skills-cursor.md).

## Синхронизация

Исходник: `prodakt/product-manager-agent-main/`. Обновление:

```bash
./prodakt/product-manager-agent-main/scripts/sync-to-cursor.sh
```

## Базовые правила

Те же, что в `using-agent-skills`: озвучивай допущения, не угадывай при путанице, дисциплина scope, верифицируй результат.

Дополнительно для PM:
- Сохраняй substantial output в markdown (`docs/pm/` по умолчанию)
- Предлагай next workflow после завершения (как в исходных commands)
- Не смешивай PM discovery со spec/code без явного запроса пользователя
