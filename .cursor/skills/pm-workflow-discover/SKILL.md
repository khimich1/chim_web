---
name: pm-workflow-discover
description: "Run a full product discovery cycle — from ideation through assumption mapping to experiment design. End-to-end PM workflow for Cursor (chains multiple pm skills). Use when the user asks for /discover or a full discover workflow."
disable-model-invocation: true
---

# PM Workflow: discover

> Cursor adaptation of Claude Code `/discover`. Invoke explicitly:
> «Следуй skill pm-workflow-discover» или `@.cursor/skills/pm-workflow-discover/SKILL.md`

## Cursor notes

- Slash commands (`/discover`) недоступны — используй этот workflow skill.
- Шаги со ссылкой на **skill-name** → прочитай `.cursor/skills/<skill-name>/SKILL.md` и следуй ему.
- Сохраняй артефакты в `docs/pm/` или корень workspace, если пользователь не указал путь.
- После завершения предложи следующий workflow из секции «Next steps» исходной команды.

---


# /discover -- Full Discovery Cycle

Run a structured product discovery process that moves from divergent thinking to focused validation. This command chains multiple skills into a single end-to-end workflow.

## Invocation

```
/discover Smart notification system for our project management tool
/discover New product: AI writing assistant for non-native speakers
/discover                    # asks what you're discovering
```

## Workflow

### Step 1: Understand the Discovery Context

Determine whether this is:
- **Existing product** — continuous discovery on a known product with real users
- **New product** — initial discovery for a concept without validated demand

Ask the user:
- What are you exploring? (product idea, feature area, opportunity space)
- What do you already know? (prior research, customer feedback, data)
- What decisions will this discovery inform? (build/kill, prioritize, pivot)

Accept context from uploaded files (research, PRDs, transcripts, data), links, or conversation.

### Step 2: Brainstorm Ideas (Divergent Phase)

Read `.cursor/skills/brainstorm-ideas-existing/SKILL.md` or `.cursor/skills/brainstorm-ideas-new/SKILL.md`:

- Generate ideas from PM, Designer, and Engineer perspectives
- Present the top 10 ideas with brief rationale
- Ask the user to select 3-5 ideas to carry forward, or accept all

**Checkpoint**: "Here are 10 ideas. Which ones should we stress-test? Pick 3-5, or I can carry all forward."

### Step 3: Identify Assumptions (Critical Thinking Phase)

For each selected idea, Read `.cursor/skills/identify-assumptions-existing/SKILL.md` or `.cursor/skills/identify-assumptions-new/SKILL.md`:

- Surface assumptions across risk categories:
  - **Value**: Will users want this?
  - **Usability**: Can users figure it out?
  - **Feasibility**: Can we build it?
  - **Viability**: Does the business case work?
  - **Go-to-Market** (new products only): Can we reach and convert users?
- Use devil's advocate multi-perspective analysis
- Compile a master list of all assumptions across all ideas

### Step 4: Prioritize Assumptions (Focus Phase)

Read and follow `.cursor/skills/prioritize-assumptions/SKILL.md`:

- Map assumptions on an Impact × Risk matrix
- Identify the "leap of faith" assumptions — high impact, high uncertainty
- Rank assumptions by test priority
- Group related assumptions that can be tested together

**Checkpoint**: "Here are your riskiest assumptions. Which ones feel most critical to validate first?"

### Step 5: Design Experiments (Validation Phase)

For the top-priority assumptions, apply **brainstorm-experiments-existing** or skill `brainstorm-experiments-new` (see `.cursor/skills/brainstorm-experiments-new/SKILL.md`):

- Design 1-2 experiments per critical assumption
- For existing products: A/B tests, fake doors, prototypes, user tests, data analysis
- For new products: XYZ hypotheses, pretotypes, landing pages, concierge MVPs
- Include success criteria, timeline, and effort for each
- Sequence experiments by dependency and effort

### Step 6: Create Discovery Plan

Compile everything into a discovery plan document:

```
## Discovery Plan: [Topic]

**Date**: [today]
**Product Stage**: [existing/new]
**Discovery Question**: [what we're trying to learn]

### Ideas Explored
[Summary of brainstormed ideas with brief descriptions]

### Selected Ideas for Validation
[3-5 ideas carried forward with rationale]

### Critical Assumptions
| # | Assumption | Category | Impact | Uncertainty | Priority |
|---|-----------|----------|--------|-------------|----------|

### Validation Experiments
| # | Tests Assumption | Method | Success Criteria | Effort | Timeline |
|---|-----------------|--------|-----------------|--------|----------|

### Experiment Details
[For each experiment: hypothesis, setup, measurement, decision criteria]

### Discovery Timeline
Week 1: [experiments]
Week 2: [experiments]
Week 3: [analysis and decision]

### Decision Framework
- If [experiment] succeeds → proceed to [next step]
- If [experiment] fails → [pivot/kill/investigate further]
```

Save the plan as a markdown file to the user's workspace.

### Step 7: Offer Next Steps

- "Want me to **create a PRD** for the top idea?"
- "Should I **design an interview script** to supplement these experiments?"
- "Want me to **set up metrics** to track the experiments?"
- "Should I **estimate effort** and create user stories for the MVP?"

## Notes

- This is a 15-30 minute structured workflow — let the user know upfront
- At each checkpoint, the user can redirect, skip, or go deeper
- If the user has research data, pull insights from it before brainstorming
- The discovery plan should be a living document — offer to update it as experiments run
- For new products, emphasize desirability validation before feasibility
- For existing products, check if there's usage data that can inform assumptions
