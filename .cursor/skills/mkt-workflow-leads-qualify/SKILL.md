---
name: mkt-workflow-leads-qualify
description: "Create lead qualification criteria. Marketing workflow for Cursor (AgentKits). Use when the user asks for /leads:qualify or a full leads qualify workflow."
disable-model-invocation: true
---

# Marketing Workflow: leads/qualify

> Cursor adaptation of AgentKits `/leads:qualify`. Invoke explicitly:
> «Следуй skill mkt-workflow-leads-qualify» или `@.cursor/skills/mkt-workflow-leads-qualify/SKILL.md`

## Cursor notes

- Slash commands (`/leads:qualify`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Prerequisites

Before running this command, ensure you have:
- [ ] Product or service defined
- [ ] Sales process understood
- [ ] Historical conversion data (if available)

## Context Loading

Load these files first:
1. `./README.md` - Product context
2. `./docs/personas/` - Buyer personas
3. `.cursor/.cursor/skills/mkt-mkt-marketing-fundamentals/SKILL.md` - Qualification frameworks

---

## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-marketing-fundamentals/SKILL.md`s.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Output Scope

**Question:** "What level of qualification framework do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - ICP definition and MQL criteria
- **Recommended** - Full framework with scoring
- **Complete** - Comprehensive with handoff protocols
- **Custom** - I'll specify what I need

---

### Step 2: Ask Business Type

**Question:** "What type of business model?"
**Header:** "Business"
**MultiSelect:** false

**Options:**
- **B2B SaaS** - Software subscriptions
- **B2B Services** - Professional services
- **B2B Enterprise** - Large deal sales
- **B2C/D2C** - Consumer products

---

### Step 3: Ask Qualification Dimensions

**Question:** "Which dimensions should we evaluate?"
**Header:** "Dimensions"
**MultiSelect:** true

**Options:**
- **Firmographic** - Company size, industry, revenue
- **Demographic** - Role, seniority, department
- **Behavioral** - Engagement, intent signals
- **Technographic** - Tech stack, integrations

---

### Step 4: Ask Sales Cycle

**Question:** "What's your typical sales cycle length?"
**Header:** "Cycle"
**MultiSelect:** false

**Options:**
- **Short (<1 month)** - Quick decisions
- **Medium (1-3 months)** - Standard B2B
- **Long (3-6 months)** - Enterprise sales
- **Complex (6+ months)** - Strategic deals

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Lead Qualification Configuration

| Parameter | Value |
|-----------|-------|
| Product/Service | [description] |
| Business Type | [selected type] |
| Dimensions | [selected dimensions] |
| Sales Cycle | [selected cycle] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Create this qualification framework?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, create framework** - Start creation
- **No, change settings** - Go back to modify

---

## Workflow

1. **ICP Definition**
   - Company characteristics
   - Industry and vertical
   - Company size/revenue
   - Technology stack
   - Budget indicators

2. **Scoring Dimensions**
   - Demographic factors
   - Firmographic factors
   - Behavioral signals
   - Engagement metrics
   - Intent indicators

3. **Threshold Setting**
   - MQL criteria
   - SQL criteria
   - Point thresholds
   - Score decay rules

4. **Disqualification Criteria**
   - Hard disqualifiers
   - Soft disqualifiers
   - Requalification paths

5. **Handoff Protocols**
   - Marketing → Sales handoff
   - Required information
   - SLA definitions

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Framework design | `lead-qualifier` | Primary task |
| ICP research | `researcher` | Data gathering |
| Handoff process | `sales-enabler` | Complete scope |

---

## Output Format

### Basic Scope

```markdown
## Lead Qualification: [Product]

### Ideal Customer Profile
- Company size: [Range]
- Industry: [List]
- Revenue: [Range]

### MQL Criteria
| Signal | Weight | Threshold |
|--------|--------|-----------|
| [Signal] | High | [Threshold] |

### Disqualifiers
- [Hard disqualifier 1]
- [Hard disqualifier 2]
```

### Recommended Scope

[Include Basic + Full scoring rubric + SQL criteria + Lead stages + Automation triggers + Success metrics]

### Complete Scope

[Include all + Handoff playbook + SLA definitions + Feedback loops + Requalification paths + CRM integration specs]

---

## Pre-Delivery Validation

Before delivering qualification framework:
- [ ] ICP clearly defined
- [ ] MQL criteria actionable
- [ ] Disqualifiers identified
- [ ] Handoff process clear
- [ ] Score thresholds set

---

## Output Location

Save framework to: `./docs/leads/qualify-[product]-[YYYY-MM-DD].md`

---

## Next Steps

After qualification framework, consider:
- `mkt-workflow-leads-score` - Design scoring model
- `mkt-workflow-leads-nurture` - Create nurture sequence
- `mkt-workflow-sales-qualify` - Qualify individual leads
