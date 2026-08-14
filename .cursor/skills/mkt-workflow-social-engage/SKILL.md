---
name: mkt-workflow-social-engage
description: "Develop social engagement strategy. Marketing workflow for Cursor (AgentKits). Use when the user asks for /social:engage or a full social engage workflow."
disable-model-invocation: true
---

# Marketing Workflow: social/engage

> Cursor adaptation of AgentKits `/social:engage`. Invoke explicitly:
> «Следуй skill mkt-workflow-social-engage» или `@.cursor/skills/mkt-workflow-social-engage/SKILL.md`

## Cursor notes

- Slash commands (`/social:engage`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Prerequisites

Before running this command, ensure you have:
- [ ] Target platform identified
- [ ] Current engagement status known
- [ ] Brand voice guidelines available

## Context Loading

Load these files first:
1. `./README.md` - Product context
2. `./docs/brand/` - Brand voice guidelines
3. `.cursor/.cursor/skills/mkt-mkt-social-media/SKILL.md` - Social frameworks

---

## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-social-media/SKILL.md` and `.cursor/.cursor/skills/mkt-mkt-marketing-fundamentals/SKILL.md`.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Output Scope

**Question:** "What level of engagement strategy do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - Response framework and templates
- **Recommended** - Full strategy with initiatives
- **Complete** - Comprehensive with metrics
- **Custom** - I'll specify focus areas

---

### Step 2: Ask Primary Platform

**Question:** "Which platform is the primary focus?"
**Header:** "Platform"
**MultiSelect:** false

**Options:**
- **LinkedIn** - Professional networking
- **Twitter/X** - Real-time engagement
- **Instagram** - Visual community
- **Multi-Platform** - Unified strategy

---

### Step 3: Ask Engagement Goals

**Question:** "What's the primary engagement goal?"
**Header:** "Goal"
**MultiSelect:** false

**Options:**
- **Community Building** - Grow engaged following
- **Brand Awareness** - Increase visibility
- **Lead Generation** - Drive conversions
- **Customer Support** - Service and retention

---

### Step 4: Ask Response Approach

**Question:** "How should responses be handled?"
**Header:** "Approach"
**MultiSelect:** false

**Options:**
- **Reactive** - Respond when mentioned
- **Proactive** - Seek engagement opportunities
- **Community-Led** - Foster peer support
- **Aggressive** - Maximum engagement

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Engagement Strategy Configuration

| Parameter | Value |
|-----------|-------|
| Platform | [selected platform] |
| Goal | [selected goal] |
| Approach | [selected approach] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Create this engagement strategy?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, create strategy** - Start creation
- **No, change settings** - Go back to modify

---

## Engagement Framework

| Type | Response Time | Approach |
|------|---------------|----------|
| Questions | < 2 hours | Helpful, link to resources |
| Complaints | < 1 hour | Empathetic, move to DM |
| Praise | < 4 hours | Thank, amplify |
| Mentions | < 4 hours | Engage, participate |

---

## Workflow

1. **Audience Analysis**
   - Content preferences
   - Engagement patterns
   - Response expectations

2. **Response Strategy**
   - Comment response flows
   - DM conversation templates
   - Escalation protocols

3. **Community Initiatives**
   - Discussion prompts
   - Polls and questions
   - Member spotlights

4. **Metrics & Goals**
   - Response time targets
   - Engagement rate goals
   - Sentiment tracking

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Strategy creation | `continuity-specialist` | Primary task |
| Response templates | `copywriter` | Template library |
| Community planning | `planner` | Initiative calendar |

---

## Output Format

### Basic Scope

```markdown
## Engagement Strategy: [Platform]

### Response Framework
| Type | Time | Response |
|------|------|----------|
| Question | <2hr | [Template] |
| Complaint | <1hr | [Template] |

### Quick Response Templates
**FAQ:** [Template]
**Appreciation:** [Template]
**Redirect:** [Template]
```

### Recommended Scope

[Include Basic + Full template library + Community initiatives + Engagement calendar]

### Complete Scope

[Include all + Metrics dashboard + Sentiment tracking + Escalation protocols + Training guide]

---

## Pre-Delivery Validation

Before delivering engagement strategy:
- [ ] Response framework clear
- [ ] Templates ready to use
- [ ] Community initiatives defined
- [ ] Escalation protocols set
- [ ] Metrics targets defined

---

## Output Location

Save strategy to: `./docs/social/engage-[platform]-[YYYY-MM-DD].md`

---

## Next Steps

After engagement strategy, consider:
- `mkt-workflow-social-schedule` - Create posting schedule
- `mkt-workflow-social-viral` - Create viral content
- `mkt-workflow-content-social` - Write social content
