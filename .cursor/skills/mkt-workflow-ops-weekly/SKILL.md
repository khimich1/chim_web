---
name: mkt-workflow-ops-weekly
description: "Weekly marketing review and planning. Marketing workflow for Cursor (AgentKits). Use when the user asks for /ops:weekly or a full ops weekly workflow."
disable-model-invocation: true
---

# Marketing Workflow: ops/weekly

> Cursor adaptation of AgentKits `/ops:weekly`. Invoke explicitly:
> «Следуй skill mkt-workflow-ops-weekly» или `@.cursor/skills/mkt-workflow-ops-weekly/SKILL.md`

## Cursor notes

- Slash commands (`/ops:weekly`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Prerequisites

Before running this command, ensure you have:
- [ ] Week to review identified
- [ ] Access to campaign data
- [ ] MCP configured: `google-analytics`, `hubspot` (optional)

## Context Loading

Load these files first:
1. `./README.md` - Product context
2. `./docs/ops/weekly/` - Previous weekly reviews
3. `docs/marketing/plans/` - Active campaign plans

---

## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Activate `marketing-fundamentals`, `analytics-attribution`, `sales-workflow.md`, `crm-workflow.md` skills.

**Components**: Reference `./.claude/components/interactive-questions.md` and `./.claude/components/date-helpers.md`

---

## Interactive Parameter Collection

### Step 0: Get Current Date (MANDATORY)

**Execute BEFORE asking any questions:**

```bash
# Get current date info
CURRENT_DATE=$(date +%Y-%m-%d)
CURRENT_WEEK=$(date +%V)
CURRENT_YEAR=$(date +%Y)

# Week boundaries
WEEK_START=$(date -v-$(($(date +%u)-1))d +%Y-%m-%d 2>/dev/null || date -d "last monday" +%Y-%m-%d)
WEEK_END=$(date -v-$(($(date +%u)-1))d -v+6d +%Y-%m-%d 2>/dev/null || date -d "next sunday" +%Y-%m-%d)

# Previous weeks
PREV_WEEK_START=$(date -v-7d -v-$(($(date +%u)-1))d +%Y-%m-%d 2>/dev/null || date -d "last monday -7 days" +%Y-%m-%d)
PREV_WEEK_END=$(date -v-7d -v-$(($(date +%u)-1))d -v+6d +%Y-%m-%d 2>/dev/null || date -d "last sunday" +%Y-%m-%d)

echo "Current Week: W$CURRENT_WEEK ($WEEK_START to $WEEK_END)"
```

---

### Step 1: Ask Output Scope

**Question:** "What level of weekly review do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - Quick metrics check and priorities
- **Recommended** - Full review with planning
- **Complete** - Comprehensive with content calendar
- **Custom** - I'll select specific sections

---

### Step 2: Ask Week Period (DYNAMIC - use Step 0 values)

**Question:** "Which week are you reviewing?"
**Header:** "Week"
**MultiSelect:** false

**Options (generated from Step 0):**
- **Current Week (W[CURRENT_WEEK])** - [WEEK_START] to [WEEK_END]
- **Last Week** - [PREV_WEEK_START] to [PREV_WEEK_END]
- **2 Weeks Ago** - For historical comparison
- **Custom week** - Enter specific dates

---

### Step 3: Ask Review Focus

**Question:** "What areas should we focus on?"
**Header:** "Focus"
**MultiSelect:** true

**Options:**
- **Performance Metrics** - Traffic, leads, conversions
- **Campaign Status** - Active campaigns progress
- **Content Review** - Content performance analysis
- **Next Week Planning** - Priorities and calendar

---

### Step 4: Ask Output Preference

**Question:** "What format do you prefer?"
**Header:** "Format"
**MultiSelect:** false

**Options:**
- **Dashboard** - Visual metrics summary
- **Report** - Detailed written report
- **Checklist** - Action-oriented task list
- **Slides** - Presentation-ready format

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Weekly Review Configuration

| Parameter | Value |
|-----------|-------|
| Week | W[week] ([dates]) |
| Scope | [Basic/Recommended/Complete] |
| Focus Areas | [selected areas] |
| Format | [selected format] |
```

**Question:** "Proceed with weekly review?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, generate review** - Start weekly review
- **No, change settings** - Go back to modify

---

## Data Reliability (MANDATORY)

**CRITICAL**: Follow `./workflows/data-reliability-rules.md` strictly.

### MCP Sources
Use MCP for metrics; if unavailable show "⚠️ NOT AVAILABLE":
- `google-analytics` - Traffic, conversions
- `hubspot` - Leads, CRM data
- `meta-ads` - Ad performance
- `twitter`, `tiktok` - Social metrics

---

## Workflow

1. **Metrics Compilation**
   - Traffic, leads, conversions
   - Email performance
   - Social engagement
   - Ad performance

2. **Progress Tracking**
   - Review completed vs planned
   - Identify blockers
   - Plan next week

3. **Content Planning**
   - Content calendar update
   - Campaign adjustments
   - Resource allocation

4. **Funnel Analysis**
   - Funnel conversion analysis (per CRM workflow benchmarks)
   - Lead quality trends
   - SLA compliance review

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Metrics compilation | `researcher` | Weekly review |
| Progress tracking | `project-manager` | Status update |
| Content planning | `planner` | Next week prep |
| Funnel analysis | `lead-qualifier` | Conversion review |

---

## Output Format

### Basic Scope

```markdown
# Weekly Review: W[X] ([Date Range])

## Key Metrics vs Targets
| Metric | Actual | Target | Status |
|--------|--------|--------|--------|
| Traffic | X | X | 🟢/🟡/🔴 |
| Leads | X | X | 🟢/🟡/🔴 |

## Top 3 Wins
1. [Win with data]

## Next Week Priorities
1. [Priority 1]
2. [Priority 2]
```

### Recommended Scope

[Include Basic + Performance Metrics + Campaign Status + Content Review + Next Week Planning]

### Complete Scope

[Include all + Content Calendar + Resource Needs + Detailed Analytics + WoW comparison]

---

## Pre-Delivery Validation

Before delivering weekly review:
- [ ] Key metrics vs targets shown
- [ ] Campaign status updated
- [ ] Content reviewed
- [ ] Next week priorities set
- [ ] Blockers identified

---

## Output Location

Save review to: `./docs/ops/weekly/W[XX]-[YYYY].md`

---

## Next Steps

After weekly review, consider:
- `mkt-workflow-ops-daily` - Daily task management
- `mkt-workflow-report-weekly` - Client-ready report
- `mkt-workflow-campaign-calendar` - Content calendar update
