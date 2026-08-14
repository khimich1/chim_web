---
name: using-marketing-skills
description: Обнаруживает и применяет Marketing skills (AgentKits Marketing). Используй при SEO, CRO, контенте, email, paid ads, кампаниях и growth-задачах chim_web/himych.ru.
---

# Использование Marketing Skills (Cursor)

## Обзор

**AgentKits Marketing** ([aitytech/agentkits-marketing](https://github.com/aitytech/agentkits-marketing)) — marketing automation kit: agents, skills, workflows. В Cursor адаптирован с префиксом **`mkt-`** (не путать с PM skills).

| Тип | Паттерн | Пример |
|-----|---------|--------|
| **Atomic skill** | `mkt-*` | `mkt-seo-mastery`, `mkt-page-cro`, `mkt-copywriting` |
| **Workflow** (бывшие `/commands`) | `mkt-workflow-*` | `mkt-workflow-campaign-plan`, `mkt-workflow-seo-audit` |
| **Persona** | `.cursor/rules/agents/mkt-*` | `mkt-copywriter`, `mkt-seo-specialist` |

Исходник: `ag_marketing/agentkits-marketing/`. Синхронизация:

```bash
./ag_marketing/agentkits-marketing/scripts/sync-to-cursor.sh
```

## Контекст chim_web

Перед marketing-задачей загрузи:
1. `docs/marketing/brand-context.md` — продукт, аудитория, каналы, KPI
2. `docs/strategy/seo-strategy.md` — SEO-архитектура
3. `frontend/app/(marketing)/` — текущие landing pages

Артефакты сохраняй в `docs/marketing/` (campaigns/, research/, content/, plans/).

## Маршрутизация

```
Marketing-задача
    │
    ├── Кампания end-to-end? ───────────→ mkt-workflow-campaign-plan
    │   ├── Brief / calendar ───────────→ mkt-workflow-campaign-brief, mkt-workflow-campaign-calendar
    │   └── Анализ кампании ────────────→ mkt-workflow-campaign-analyze
    │
    ├── SEO? ───────────────────────────→ mkt-seo-mastery (atomic)
    │   ├── Keyword research ───────────→ mkt-workflow-seo-keywords
    │   ├── SEO audit ──────────────────→ mkt-workflow-seo-audit
    │   ├── On-page optimize ───────────→ mkt-workflow-seo-optimize
    │   ├── Programmatic SEO ───────────→ mkt-workflow-seo-programmatic + mkt-programmatic-seo
    │   └── Schema markup ──────────────→ mkt-workflow-seo-schema + mkt-schema-markup
    │
    ├── Landing / CRO? ─────────────────→ mkt-page-cro (atomic)
    │   ├── Page audit ─────────────────→ mkt-workflow-cro-page
    │   ├── Form (запись) ──────────────→ mkt-workflow-cro-form
    │   ├── Signup flow ────────────────→ mkt-workflow-cro-signup
    │   └── A/B test setup ─────────────→ mkt-workflow-test-ab-setup
    │
    ├── Контент? ───────────────────────→ mkt-copywriting, mkt-content-strategy
    │   ├── Landing copy ───────────────→ mkt-workflow-content-landing
    │   ├── Blog ───────────────────────→ mkt-workflow-content-blog
    │   ├── Email ──────────────────────→ mkt-workflow-content-email
    │   ├── VK/social ads ──────────────→ mkt-workflow-content-ads + mkt-paid-advertising
    │   └── Editing ────────────────────→ mkt-workflow-content-editing
    │
    ├── Email sequences? ───────────────→ mkt-email-sequence, mkt-email-marketing
    │   ├── Welcome ────────────────────→ mkt-workflow-sequence-welcome
    │   └── Nurture / re-engage ────────→ mkt-workflow-sequence-nurture, mkt-workflow-sequence-re-engage
    │
    ├── Growth / launch? ───────────────→ mkt-workflow-growth-launch + mkt-launch-strategy
    │   ├── Referral ───────────────────→ mkt-workflow-growth-referral
    │   └── Free tool (lead magnet) ────→ mkt-workflow-growth-free-tool
    │
    ├── Research / competitor? ─────────→ mkt-workflow-research-market, mkt-workflow-competitor-deep
    │
    ├── Analytics / ROI? ───────────────→ mkt-analytics-attribution
    │   ├── Funnel ─────────────────────→ mkt-workflow-analytics-funnel
    │   └── Weekly/monthly report ──────→ mkt-workflow-report-weekly, mkt-workflow-report-monthly
    │
    ├── Идеи / тактики (140 шт)? ───────→ mkt-marketing-ideas  ⚠️ НЕ pm marketing-ideas (5 идей)
    │
    └── Pricing / packaging (SaaS-style)? → mkt-pricing-strategy  ⚠️ НЕ pm pricing-strategy
```

## Связь PM ↔ Marketing

| PM skill | Marketing skill | Когда |
|----------|-----------------|-------|
| `pm-workflow-discover` | `mkt-workflow-research-market` | Discovery → execution |
| `pm-workflow-plan-launch` | `mkt-workflow-campaign-plan` | GTM → кампания |
| `pm-workflow-competitive-analysis` | `mkt-workflow-competitor-deep` | Конкуренты |
| `north-star-metric` | `mkt-analytics-attribution` | Метрики → отчёты |
| `marketing-ideas` (PM, 5 идей) | `mkt-marketing-ideas` (140 тактик) | Разный scope! |
| `pricing-strategy` (PM, product) | `mkt-pricing-strategy` (SaaS/CRO) | Разный фокус |

## Personas (agents)

| Persona | Когда |
|---------|-------|
| `mkt-copywriter` | Hero, email, social, ads copy |
| `mkt-seo-specialist` | SEO audit, keywords, technical |
| `mkt-conversion-optimizer` | CRO landing, forms, funnels |
| `mkt-attraction-specialist` | TOFU, lead gen, SEO content |
| `mkt-brand-voice-guardian` | Консистентность бренда |
| `mkt-email-wizard` | Email sequences |
| `mkt-researcher` | Market/competitor research |
| `mkt-planner` | Campaign timeline, calendar |

Вызов: «Review по @.cursor/rules/agents/mkt-copywriter.md»

## Как вызывать

```
Следуй skill mkt-workflow-campaign-plan для VK кампании август 2026
@.cursor/skills/mkt-seo-mastery/SKILL.md — аудит /zapis
Следуй skill mkt-workflow-cro-form для frontend/app/(marketing)/zapis/page.tsx
```

**Workflow skills** (`mkt-workflow-*`) — только по явному запросу (`disable-model-invocation: true`).

**Atomic skills** — подгружаются по description, когда релевантны.

## Правила качества (из AgentKits)

- **Язык:** отвечай на языке пользователя (chim_web — русский по умолчанию)
- **Данные:** MCP/API → ✅; файл → 📊; нет данных → ⚠️ NOT AVAILABLE. **Не выдумывай метрики**
- **Copy:** readability 6–8 grade, benefit-first, один primary CTA
- **Compliance:** GDPR/152-ФЗ для форм; CAN-SPAM для email

## Приоритет для chim_web (авг 2026)

1. `mkt-seo-mastery`, `mkt-programmatic-seo`, `mkt-schema-markup`
2. `mkt-page-cro`, `mkt-workflow-cro-form`, `mkt-workflow-content-landing`
3. `mkt-paid-advertising`, `mkt-workflow-content-ads`
4. `mkt-workflow-campaign-plan`, `mkt-workflow-growth-launch`

План: `docs/pm/plan-3months-ads-2026-08-10.md`

## Документация

Полная карта: [`docs/marketing-skills-cursor.md`](../../docs/marketing-skills-cursor.md)
