---
name: mkt-workflow-crm-segment
description: "Create or analyze customer segment. Marketing workflow for Cursor (AgentKits). Use when the user asks for /crm:segment or a full crm segment workflow."
disable-model-invocation: true
---

# Marketing Workflow: crm/segment

> Cursor adaptation of AgentKits `/crm:segment`. Invoke explicitly:
> «Следуй skill mkt-workflow-crm-segment» или `@.cursor/skills/mkt-workflow-crm-segment/SKILL.md`

## Cursor notes

- Slash commands (`/crm:segment`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Prerequisites

Before running this command, ensure you have:
- [ ] Segment criteria or name defined
- [ ] Use case for segment identified
- [ ] MCP configured: `hubspot` (optional)

## Context Loading

Load these files first:
1. `./README.md` - Product context
2. `./docs/personas/` - Buyer personas
3. `.cursor/.cursor/skills/mkt-mkt-marketing-fundamentals/SKILL.md` - Segmentation frameworks

---

## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-marketing-fundamentals/SKILL.md` and `.cursor/.cursor/skills/mkt-mkt-analytics-attribution/SKILL.md`.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Output Scope

**Question:** "What level of segment analysis do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - Segment definition and criteria
- **Recommended** - Full analysis with strategy
- **Complete** - Comprehensive with automation
- **Custom** - I'll specify what I need

---

### Step 2: Ask Segment Action

**Question:** "What do you want to do with this segment?"
**Header:** "Action"
**MultiSelect:** false

**Options:**
- **Create** - Define new segment criteria
- **Analyze** - Assess existing segment
- **Optimize** - Improve segment performance
- **Compare** - Benchmark segments

---

### Step 3: Ask Segment Type

**Question:** "What type of segment is this?"
**Header:** "Type"
**MultiSelect:** false

**Options:**
- **Demographic** - Based on who they are
- **Behavioral** - Based on what they do
- **Lifecycle** - Based on customer stage
- **Value-Based** - Based on revenue potential

---

### Step 4: Ask Primary Use Case

**Question:** "What's the primary use case for this segment?"
**Header:** "Use Case"
**MultiSelect:** false

**Options:**
- **Email Campaigns** - Targeted email marketing
- **Lead Nurturing** - Sequence targeting
- **Sales Outreach** - Sales prioritization
- **Reporting** - Performance analysis

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Segment Configuration

| Parameter | Value |
|-----------|-------|
| Segment | [description] |
| Action | [selected action] |
| Type | [selected type] |
| Use Case | [selected use case] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Create/analyze this segment?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, proceed** - Start analysis
- **No, change settings** - Go back to modify

---

## Workflow

1. **Segment Definition**
   - Demographic criteria
   - Behavioral criteria
   - Engagement criteria
   - Lifecycle stage

2. **Segment Analysis**
   - Size estimation
   - Value potential
   - Engagement patterns
   - Conversion likelihood

3. **Strategy Development**
   - Content recommendations
   - Channel priorities
   - Personalization approach

4. **Automation Setup**
   - Entry/exit criteria
   - Sequence assignment
   - Score adjustments

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Segment definition | `lead-qualifier` | Primary task |
| Engagement analysis | `continuity-specialist` | Behavioral data |
| Campaign strategy | `email-wizard` | Automation setup |

---

## Output Format

### Basic Scope

```markdown
## Segment: [Name]

### Definition
| Type | Criteria | Value |
|------|----------|-------|
| Demographic | [Field] | [Condition] |
| Behavioral | [Action] | [Threshold] |

### Exclusions
- [Exclusion 1]
- [Exclusion 2]

### Estimated Size
- Contacts: [Number]
```

### Recommended Scope

[Include Basic + Full analysis + Engagement profile + Conversion patterns + Content recommendations]

### Complete Scope

[Include all + Automation setup + Personalization strategy + A/B test plan + Performance metrics]

---

## Pre-Delivery Validation

Before delivering segment:
- [ ] Criteria clearly defined
- [ ] Size estimated
- [ ] Use case alignment confirmed
- [ ] Exclusions documented
- [ ] Entry/exit conditions set

---

## Output Location

Save segment to: `./docs/crm/segment-[name]-[YYYY-MM-DD].md`

---

## Next Steps

After segment creation, consider:
- `mkt-workflow-crm-sequence` - Create segment-specific sequence
- `mkt-workflow-leads-nurture` - Design nurture for segment
- `mkt-workflow-content-email` - Create targeted email copy
