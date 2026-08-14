---
name: mkt-workflow-marketing-psychology
description: "Apply psychological principles and mental models to marketing. Marketing workflow for Cursor (AgentKits). Use when the user asks for /marketing:psychology or a full marketing psychology workflow."
disable-model-invocation: true
---

# Marketing Workflow: marketing/psychology

> Cursor adaptation of AgentKits `/marketing:psychology`. Invoke explicitly:
> «Следуй skill mkt-workflow-marketing-psychology» или `@.cursor/skills/mkt-workflow-marketing-psychology/SKILL.md`

## Cursor notes

- Slash commands (`/marketing:psychology`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Prerequisites

Before running this command, ensure you have:
- [ ] Marketing challenge clearly defined
- [ ] Context for application (page, email, pricing, etc.)

## Context Loading

Load these files first:
1. `./README.md` - Product context
2. `.cursor/.cursor/skills/mkt-mkt-marketing-psychology/SKILL.md` - 70+ mental models
3. `.cursor/.cursor/skills/mkt-mkt-marketing-fundamentals/SKILL.md` - Marketing frameworks

---

## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-marketing-psychology/SKILL.md` and `.cursor/.cursor/skills/mkt-mkt-marketing-fundamentals/SKILL.md`.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Output Scope

**Question:** "What level of psychology guidance do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - Top models with applications
- **Recommended** - Full analysis with examples
- **Complete** - Comprehensive with implementation
- **Custom** - I'll specify focus areas

---

### Step 2: Ask Challenge Type

**Question:** "What marketing challenge are you facing?"
**Header:** "Challenge"
**MultiSelect:** false

**Options:**
- **Conversion** - Low conversions, cart abandonment
- **Pricing** - Objections, value perception
- **Trust** - Credibility, authority building
- **Retention** - Churn, engagement decline

---

### Step 3: Ask Application Context

**Question:** "Where will you apply these principles?"
**Header:** "Context"
**MultiSelect:** true

**Options:**
- **Landing Pages** - Headlines, CTAs, layout
- **Pricing** - Tiers, anchoring, framing
- **Email** - Subject lines, sequences
- **Product** - Onboarding, features

---

### Step 4: Ask Depth Level

**Question:** "How deep should the psychology analysis go?"
**Header:** "Depth"
**MultiSelect:** false

**Options:**
- **Quick Reference** - Top models, fast tips
- **Standard** - Explained with examples
- **Deep Dive** - Research-backed, case studies
- **Implementation** - Step-by-step application

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Marketing Psychology Configuration

| Parameter | Value |
|-----------|-------|
| Challenge | [description] |
| Challenge Type | [selected type] |
| Application Context | [selected context] |
| Depth | [selected depth] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Analyze with these psychology principles?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, analyze** - Start analysis
- **No, change settings** - Go back to modify

---

## Quick Reference

| Challenge | Relevant Models |
|-----------|-----------------|
| Low conversions | Hick's Law, Activation Energy, BJ Fogg, Friction |
| Price objections | Anchoring, Framing, Mental Accounting, Loss Aversion |
| Building trust | Authority, Social Proof, Reciprocity, Pratfall Effect |
| Increasing urgency | Scarcity, Loss Aversion, Zeigarnik Effect |
| Retention/churn | Endowment Effect, Switching Costs, Status-Quo Bias |
| Growth stalling | Theory of Constraints, Local vs Global Optima |
| Decision paralysis | Paradox of Choice, Default Effect, Nudge Theory |
| Onboarding | Goal-Gradient, IKEA Effect, Commitment & Consistency |

---

## Model Categories

### Foundational Thinking
First Principles, Jobs to Be Done, Pareto (80/20), Inversion, Occam's Razor

### Buyer Psychology
Fundamental Attribution Error, Mere Exposure, Availability Heuristic, Confirmation Bias, Mimetic Desire

### Behavior & Persuasion
Reciprocity, Commitment & Consistency, Authority, Scarcity, Loss Aversion, Anchoring

### Pricing Psychology
Charm Pricing, Rule of 100, Price Relativity, Mental Accounting

### Growth & Scale
Feedback Loops, Compounding, Network Effects, Flywheel, Switching Costs

---

## Workflow

1. **Challenge Identification**
   - Define the specific marketing problem
   - Identify symptoms and root causes
   - Establish success metrics

2. **Model Matching**
   - Select relevant mental models
   - Explain psychological foundations
   - Map to marketing context

3. **Application Design**
   - Translate theory to tactics
   - Provide specific implementations
   - Include real-world examples

4. **Ethical Implementation**
   - Ensure transparent application
   - Balance persuasion with value
   - Avoid dark patterns

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Psychology analysis | `brainstormer` | Primary task |
| Copy applications | `copywriter` | Messaging tactics |
| CRO implementation | `conversion-optimizer` | Conversion focus |

---

## Output Format

### Basic Scope

```markdown
## Psychology Analysis: [Challenge]

### Top 3 Models

1. **[Model Name]**
   - Definition: [Brief]
   - Application: [Specific action]

2. **[Model Name]**
   - Definition: [Brief]
   - Application: [Specific action]

### Quick Implementation
[Immediate action based on principles]
```

### Recommended Scope

[Include Basic + 5-7 models + Detailed examples + Before/after comparisons + Implementation checklist]

### Complete Scope

[Include all + Full model library reference + Case studies + A/B test suggestions + Measurement framework]

---

## Output Location

Save analysis to: `./docs/marketing/psychology-[challenge]-[YYYY-MM-DD].md`

---

## Pre-Delivery Validation

Before delivering psychology analysis:
- [ ] Models match the challenge type
- [ ] Applications are specific and actionable
- [ ] Examples provided for each principle
- [ ] Ethical implementation noted
- [ ] Before/after comparisons included

---

## Next Steps

After psychology analysis, consider:
- `mkt-workflow-cro-page` - Apply principles to pages
- `mkt-workflow-content-landing` - Create optimized landing page
- `mkt-workflow-pricing-strategy` - Apply to pricing
