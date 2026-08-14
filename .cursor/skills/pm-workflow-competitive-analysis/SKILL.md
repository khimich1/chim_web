---
name: pm-workflow-competitive-analysis
description: "Analyze the competitive landscape — identify competitors, compare strengths and weaknesses, find differentiation opportunities. End-to-end PM workflow for Cursor (chains multiple pm skills). Use when the user asks for /competitive-analysis or a full competitive-analysis workflow."
disable-model-invocation: true
---

# PM Workflow: competitive-analysis

> Cursor adaptation of Claude Code `/competitive-analysis`. Invoke explicitly:
> «Следуй skill pm-workflow-competitive-analysis» или `@.cursor/skills/pm-workflow-competitive-analysis/SKILL.md`

## Cursor notes

- Slash commands (`/competitive-analysis`) недоступны — используй этот workflow skill.
- Шаги со ссылкой на **skill-name** → прочитай `.cursor/skills/<skill-name>/SKILL.md` и следуй ему.
- Сохраняй артефакты в `docs/pm/` или корень workspace, если пользователь не указал путь.
- После завершения предложи следующий workflow из секции «Next steps» исходной команды.

---


# /competitive-analysis -- Competitive Landscape Analysis

Research and analyze your competitive landscape. Identifies direct and indirect competitors, maps positioning, and surfaces differentiation opportunities.

## Invocation

```
/competitive-analysis AI-powered project management tools
/competitive-analysis Our product vs Notion, Asana, and Monday.com
/competitive-analysis [upload a competitor list or market brief]
```

## Workflow

### Step 1: Understand the Competitive Context

Ask:
- What is your product? What category does it compete in?
- Any specific competitors you want analyzed? Or should I identify them?
- What's the lens? (feature comparison, positioning, pricing, go-to-market)
- What will you use this analysis for? (strategy, sales enablement, investor pitch, product roadmap)

### Step 2: Identify Competitors

Read and follow `.cursor/skills/competitor-analysis/SKILL.md`:

- Identify 5 direct competitors (same category, same buyer)
- Identify 2-3 indirect competitors (different approach, same job-to-be-done)
- Note emerging/disruptive players if relevant
- Use web research to gather current information

### Step 3: Analyze Each Competitor

For each competitor:
- **Positioning**: How they describe themselves, target audience, key messaging
- **Strengths**: What they do well, where they win
- **Weaknesses**: Where they fall short, common complaints
- **Pricing**: Model and price points (if public)
- **Market traction**: Funding, team size, customer base signals
- **Recent moves**: New features, partnerships, pivots

### Step 4: Generate Competitive Analysis

```
## Competitive Analysis: [Your Product/Market]

**Date**: [today]
**Analyzed**: [count] competitors

### Market Overview
[2-3 sentences on market dynamics, trends, and where it's heading]

### Competitive Landscape
| Competitor | Category | Target | Positioning | Strength | Weakness |
|-----------|----------|--------|------------|----------|----------|

### Feature Comparison Matrix
| Capability | Your Product | Competitor A | Competitor B | Competitor C |
|-----------|-------------|-------------|-------------|-------------|

### Positioning Map
[2x2 matrix showing competitive positioning on key dimensions]

### Differentiation Opportunities
1. **[Opportunity]** — [why it's defensible and valuable]
2. ...

### Competitive Threats
1. **[Threat]** — [what to watch for, recommended response]
2. ...

### Recommendations
- **Double down on**: [your unique advantages]
- **Close the gap on**: [table-stakes features you're missing]
- **Ignore**: [competitor moves that aren't worth responding to]
```

Save as markdown.

### Step 5: Offer Next Steps

- "Want me to **create a battlecard** for sales against a specific competitor?"
- "Should I **develop positioning** that differentiates from the top competitors?"
- "Want me to **identify feature gaps** to close and add to the roadmap?"

## Notes

- Web research is used for current competitor data — results are as fresh as available sources
- Distinguish between "table stakes" (must-have to compete) and "differentiators" (must-have to win)
- Don't just list features — analyze *why* competitors make the choices they make
- Pricing intelligence should note whether pricing is public, usage-based, or requires sales contact
- Update this analysis quarterly — competitive landscapes shift fast
