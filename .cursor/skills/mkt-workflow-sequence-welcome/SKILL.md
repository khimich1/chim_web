---
name: mkt-workflow-sequence-welcome
description: "Create welcome email sequence for new subscribers. Marketing workflow for Cursor (AgentKits). Use when the user asks for /sequence:welcome or a full sequence welcome workflow."
disable-model-invocation: true
---

# Marketing Workflow: sequence/welcome

> Cursor adaptation of AgentKits `/sequence:welcome`. Invoke explicitly:
> «Следуй skill mkt-workflow-sequence-welcome» или `@.cursor/skills/mkt-workflow-sequence-welcome/SKILL.md`

## Cursor notes

- Slash commands (`/sequence:welcome`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Prerequisites

Before running this command, ensure you have:
- [ ] Brand/product defined
- [ ] Target audience identified
- [ ] Sequence goal clear

## Context Loading

Load these files first:
1. `./README.md` - Product context
2. `./docs/sequences/` - Existing sequences
3. `.cursor/.cursor/skills/mkt-mkt-email-sequence/SKILL.md` - Sequence frameworks

---

## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-email-marketing/SKILL.md`, `.cursor/.cursor/skills/mkt-mkt-email-sequence/SKILL.md`, `.cursor/.cursor/skills/mkt-mkt-marketing-fundamentals/SKILL.md`.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Output Scope

**Question:** "What level of welcome sequence do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - 3-email welcome series
- **Recommended** - 5-email sequence with automation
- **Complete** - Full sequence with A/B variants
- **Custom** - I'll specify parameters

---

### Step 2: Ask Sequence Goal

**Question:** "What's the primary goal of this welcome sequence?"
**Header:** "Goal"
**MultiSelect:** false

**Options:**
- **Engagement** - Build relationship and trust
- **Education** - Teach about product/service
- **Conversion** - Drive to purchase/trial
- **Onboarding** - Guide to first success

---

### Step 3: Ask Audience Type

**Question:** "Who is this welcome sequence for?"
**Header:** "Audience"
**MultiSelect:** false

**Options:**
- **Newsletter** - Content subscribers
- **Lead Magnet** - Downloaded resource
- **Trial Signup** - Product trial users
- **Purchase** - New customers

---

### Step 4: Ask Sequence Length

**Question:** "How many emails in the sequence?"
**Header:** "Length"
**MultiSelect:** false

**Options:**
- **Short (3)** - Quick welcome and value
- **Standard (5)** - Full welcome journey
- **Extended (7)** - Deep engagement
- **Custom** - I'll specify count

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Welcome Sequence Configuration

| Parameter | Value |
|-----------|-------|
| Brand/Product | [description] |
| Goal | [selected goal] |
| Audience | [selected audience] |
| Length | [selected length] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Create this welcome sequence?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, create sequence** - Start creation
- **No, change settings** - Go back to modify

---

## Best Practices

- Complete within 7 days (engagement peaks early)
- First email: immediate (<5 min SLA per speed-to-lead research)
- Progressive value delivery
- Single CTA per email
- Mobile-first design

---

## Workflow

1. **Sequence Design**
   - Timing and triggers
   - Subject line variants (A/B)
   - Email structure

2. **Content Creation**
   - Compelling subject lines
   - Engaging body copy
   - Clear CTAs

3. **Automation Setup**
   - Segment triggers
   - Exit conditions
   - Success metrics

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Sequence design | `email-wizard` | Primary task |
| Copy writing | `copywriter` | Email content |
| Segmentation | `lead-qualifier` | Entry/exit criteria |

---

## Output Format

### Basic Scope

```markdown
## Welcome Sequence: [Brand]

### Overview
- Trigger: New signup
- Duration: 7 days (3 emails)

### Email 1: Welcome (Immediate)
**Subject A:** [Subject line]
**Subject B:** [Variant]
**Body:** [Copy]
**CTA:** [Action]

### Email 2: Value (Day 2)
[Structure]

### Email 3: Engagement (Day 5)
[Structure]
```

### Recommended Scope

[Include Basic + 5 emails + Full automation logic + Success metrics + Exit conditions]

### Complete Scope

[Include all + A/B variants for all + Personalization tokens + Segment variations + Analytics setup]

---

## Pre-Delivery Validation

Before delivering welcome sequence:
- [ ] First email immediate (<5 min)
- [ ] Value delivered progressively
- [ ] Single CTA per email
- [ ] Exit conditions set
- [ ] Success metrics defined

---

## Output Location

Save sequence to: `./docs/sequences/welcome-[brand]-[YYYY-MM-DD].md`

---

## Next Steps

After welcome sequence, consider:
- `mkt-workflow-sequence-nurture` - Create nurture sequence
- `mkt-workflow-cro-onboarding` - Optimize onboarding
- `mkt-workflow-content-email` - Write detailed email copy
