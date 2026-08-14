---
name: pm-workflow-market-product
description: "Brainstorm marketing ideas, positioning, value prop statements, and product names — creative marketing toolkit. End-to-end PM workflow for Cursor (chains multiple pm skills). Use when the user asks for /market-product or a full market-product workflow."
disable-model-invocation: true
---

# PM Workflow: market-product

> Cursor adaptation of Claude Code `/market-product`. Invoke explicitly:
> «Следуй skill pm-workflow-market-product» или `@.cursor/skills/pm-workflow-market-product/SKILL.md`

## Cursor notes

- Slash commands (`/market-product`) недоступны — используй этот workflow skill.
- Шаги со ссылкой на **skill-name** → прочитай `.cursor/skills/<skill-name>/SKILL.md` и следуй ему.
- Сохраняй артефакты в `docs/pm/` или корень workspace, если пользователь не указал путь.
- После завершения предложи следующий workflow из секции «Next steps» исходной команды.

---


# /market-product -- Marketing Creative Toolkit

Generate creative marketing assets: campaign ideas, positioning statements, value prop copy, and product naming options. All in one workflow or pick specific modules.

## Invocation

```
/market-product AI scheduling tool for remote teams — need launch marketing
/market-product Help me position our analytics product against enterprise competitors
/market-product We need a name for our new developer productivity feature
```

## Workflow

### Step 1: Understand the Marketing Need

Ask:
- What is the product? Target audience?
- What do you need? (full marketing toolkit, or specific: ideas, positioning, naming, copy)
- What's the context? (launch, rebrand, campaign, competitive repositioning)
- Any existing brand guidelines or tone of voice?

### Step 2: Generate Based on Need

**Marketing Ideas** — Read and follow `.cursor/skills/marketing-ideas/SKILL.md`:
- 5 creative, cost-effective campaign ideas
- Each with: channel, messaging angle, engagement rationale, estimated effort
- Mix of quick wins and bigger bets

**Positioning** — Read and follow `.cursor/skills/positioning-ideas/SKILL.md`:
- Identify top 5 competitors for positioning context
- Generate 3-5 positioning statements differentiated from each
- Include rationale for each positioning angle

**Value Proposition Statements** — Read and follow `.cursor/skills/value-prop-statements/SKILL.md`:
- Generate copy for marketing, sales, and onboarding contexts
- Segment-specific variations
- Short (tagline), medium (elevator pitch), and long (landing page) versions

**Product Naming** — Read and follow `.cursor/skills/product-name/SKILL.md`:
- Brainstorm 5 unique, memorable names
- Each with: rationale, brand alignment, domain availability notes
- Check for unintended meanings or conflicts

### Step 3: Generate Output

```
## Marketing Toolkit: [Product]

**Date**: [today]
**Context**: [launch / rebrand / campaign / etc.]

### Marketing Campaign Ideas
| # | Idea | Channel | Effort | Expected Impact |
|---|------|---------|--------|----------------|

### Positioning Options
| # | Positioning | vs Competitor | Strength | Risk |
|---|-----------|--------------|----------|------|

**Recommended positioning**: [which and why]

### Value Prop Copy
**Tagline**: [one line]
**Elevator pitch**: [2-3 sentences]
**Landing page hero**: [headline + subheading]
**Sales one-liner**: [for sales conversations]

### Product Name Options (if requested)
| # | Name | Rationale | Domain | Risk |
|---|------|----------|--------|------|

### Messaging Matrix
| Audience | Key Message | Proof Point | CTA |
|----------|-----------|------------|-----|
```

Save as markdown.

### Step 4: Offer Next Steps

- "Want me to **draft full marketing content** (blog post, email, social)?"
- "Should I **define the North Star metric** for this campaign?"
- "Want me to **create a competitive battlecard** to support positioning?"
- "Should I **plan the full launch**?"

## Notes

- Positioning should be tested, not assumed — recommend A/B testing headlines
- Value prop copy should use the customer's language, not internal jargon
- Marketing ideas should be specific and actionable, not generic ("use social media")
- Product names should be checked for trademark conflicts before committing
- Always tie marketing back to customer JTBD, not product features
