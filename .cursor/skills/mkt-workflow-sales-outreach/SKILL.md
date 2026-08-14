---
name: mkt-workflow-sales-outreach
description: "Generate personalized outreach sequence. Marketing workflow for Cursor (AgentKits). Use when the user asks for /sales:outreach or a full sales outreach workflow."
disable-model-invocation: true
---

# Marketing Workflow: sales/outreach

> Cursor adaptation of AgentKits `/sales:outreach`. Invoke explicitly:
> «Следуй skill mkt-workflow-sales-outreach» или `@.cursor/skills/mkt-workflow-sales-outreach/SKILL.md`

## Cursor notes

- Slash commands (`/sales:outreach`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Prerequisites

Before running this command, ensure you have:
- [ ] Prospect information available
- [ ] Target persona defined
- [ ] Outreach channels identified

## Context Loading

Load these files first:
1. `./README.md` - Product context
2. `./docs/personas/` - Target buyer profiles
3. `.cursor/.cursor/skills/mkt-mkt-email-sequence/SKILL.md` - Sequence frameworks

---

## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-email-marketing/SKILL.md` and `.cursor/.cursor/skills/mkt-mkt-copywriting/SKILL.md`.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Output Scope

**Question:** "What level of outreach sequence do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - 3-touch sequence with templates
- **Recommended** - Full sequence with personalization
- **Complete** - Multi-channel with A/B variants
- **Custom** - I'll specify parameters

---

### Step 2: Ask Sequence Type

**Question:** "What's the prospect's current engagement level?"
**Header:** "Type"
**MultiSelect:** false

**Options:**
- **Cold** - No prior engagement (7 touches)
- **Warm** - Some engagement (5 touches)
- **Hot** - High intent shown (3 touches)
- **Re-engage** - Gone quiet after interest

---

### Step 3: Ask Channels

**Question:** "Which outreach channels should we use?"
**Header:** "Channels"
**MultiSelect:** true

**Options:**
- **Email** - Primary email outreach
- **LinkedIn** - Connection and messages
- **Phone** - Call scripts
- **Video** - Personalized video messages

---

### Step 4: Ask Personalization Level

**Question:** "How personalized should the outreach be?"
**Header:** "Personal"
**MultiSelect:** false

**Options:**
- **Template** - Standard templates with merge fields
- **Semi-Personal** - Industry/role customization
- **Highly Personal** - Individual research-based
- **Account-Based** - Full ABM approach

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Outreach Sequence Configuration

| Parameter | Value |
|-----------|-------|
| Prospect | [prospect info] |
| Sequence Type | [selected type] |
| Channels | [selected channels] |
| Personalization | [selected level] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Create this outreach sequence?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, create sequence** - Start creation
- **No, change settings** - Go back to modify

---

## Workflow

1. **Prospect Research**
   - Recent company news
   - LinkedIn activity
   - Pain points in their industry
   - Mutual connections

2. **Sequence Design**
   - Touch cadence and timing
   - Channel mix strategy
   - Escalation points

3. **Content Creation**
   - Personalized subject lines
   - Value-focused copy
   - Strategic follow-ups
   - Breakup message

4. **Optimization**
   - Hook refinement
   - CTA clarity
   - Personalization tokens

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Prospect research | `researcher` | Data gathering |
| Sequence creation | `sales-enabler` | Primary task |
| Copy optimization | `copywriter` | Email refinement |

---

## Output Format

### Basic Scope

```markdown
## Outreach Sequence: [Prospect]

### Sequence Type: [Cold/Warm/Hot]

### Day 1: Initial Email
**Subject:** [Subject line]
**Body:** [Email copy]

### Day 3: Follow-up
**Subject:** [Subject line]
**Body:** [Email copy]

### Day 7: Breakup
**Subject:** [Subject line]
**Body:** [Email copy]
```

### Recommended Scope

[Include Basic + Full prospect research + All touchpoints + LinkedIn scripts + Personalization hooks]

### Complete Scope

[Include all + A/B subject lines + Phone scripts + Video scripts + Objection handling + CRM automation notes]

---

## Pre-Delivery Validation

Before delivering outreach sequence:
- [ ] Personalization tokens clear
- [ ] Subject lines compelling
- [ ] CTAs specific and clear
- [ ] Timing and cadence appropriate
- [ ] Breakup message included

---

## Output Location

Save outreach to: `./docs/sales/outreach-[prospect]-[YYYY-MM-DD].md`

---

## Next Steps

After outreach sequence, consider:
- `mkt-workflow-sales-pitch` - Create sales pitch for demos
- `mkt-workflow-sales-qualify` - Qualify leads as they respond
- `mkt-workflow-crm-sequence` - Set up CRM automation
