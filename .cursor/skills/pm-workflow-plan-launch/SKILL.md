---
name: pm-workflow-plan-launch
description: "Create a full go-to-market strategy — beachhead segment, ICP, messaging, channels, and launch plan. End-to-end PM workflow for Cursor (chains multiple pm skills). Use when the user asks for /plan-launch or a full plan-launch workflow."
disable-model-invocation: true
---

# PM Workflow: plan-launch

> Cursor adaptation of Claude Code `/plan-launch`. Invoke explicitly:
> «Следуй skill pm-workflow-plan-launch» или `@.cursor/skills/pm-workflow-plan-launch/SKILL.md`

## Cursor notes

- Slash commands (`/plan-launch`) недоступны — используй этот workflow skill.
- Шаги со ссылкой на **skill-name** → прочитай `.cursor/skills/<skill-name>/SKILL.md` и следуй ему.
- Сохраняй артефакты в `docs/pm/` или корень workspace, если пользователь не указал путь.
- После завершения предложи следующий workflow из секции «Next steps» исходной команды.

---


# /plan-launch -- Go-to-Market Strategy

Build a complete GTM plan from first principles: identify your beachhead market, define the ideal customer, craft messaging, choose channels, and create a launch timeline.

## Invocation

```
/plan-launch AI-powered proposal writer for consulting firms
/plan-launch New enterprise tier for our project management tool
/plan-launch [upload a PRD, strategy doc, or pitch deck]
```

## Workflow

### Step 1: Understand the Launch

Ask:
- What are you launching? (new product, new feature, new tier, market expansion)
- What stage? (pre-launch planning, imminent launch, post-launch optimization)
- Do you have existing customers? Or starting from zero?
- What's the timeline? Any hard deadlines?
- Budget constraints? Team size?

### Step 2: Define Beachhead Segment

Read and follow `.cursor/skills/beachhead-segment/SKILL.md`:

- Evaluate potential market segments against:
  - Burning pain (how urgently they need this)
  - Willingness to pay (budget and purchase authority)
  - Winnable market share (can you reach and win them)
  - Referral potential (will they tell others)
- Recommend the single best starting segment with rationale
- Map adjacent segments for expansion after beachhead is secured

### Step 3: Define Ideal Customer Profile

Read and follow `.cursor/skills/ideal-customer-profile/SKILL.md`:

- Demographics: company size, industry, geography, tech stack
- Behaviors: how they discover solutions, buying process, decision makers
- JTBD: specific jobs they're hiring your product for
- Current alternatives: what they use today and why it falls short
- Qualification criteria: how to identify them quickly

### Step 4: Build GTM Strategy

Read and follow `.cursor/skills/gtm-strategy/SKILL.md`:

- **Positioning**: How you describe yourself to this segment
- **Messaging**: Key messages for different stakeholders (buyer, user, influencer)
- **Channels**: Where and how to reach your ICP (ranked by expected ROI)
- **Launch tactics**: Specific actions for pre-launch, launch day, and post-launch
- **Pricing alignment**: How pricing supports the GTM motion
- **Success metrics**: How you'll know the launch worked

### Step 5: Generate GTM Plan

```
## Go-to-Market Plan: [Product/Feature]

**Launch date**: [target]
**Type**: [new product / feature / tier / market expansion]

### Beachhead Segment
**Who**: [specific segment definition]
**Why them first**: [rationale against criteria]
**Size**: [TAM/SAM/SOM estimate]

### Ideal Customer Profile
| Attribute | Definition |
|-----------|-----------|
| Company size | [range] |
| Industry | [specific] |
| Decision maker | [title/role] |
| Key JTBD | [job they need done] |
| Current solution | [what they use today] |
| Qualification signal | [how to identify them] |

### Positioning & Messaging
**Positioning statement**: For [who] who [need], [product] is [category] that [benefit]. Unlike [alternative], we [differentiator].

**Key messages by stakeholder**:
| Audience | Message | Proof Point |
|----------|---------|------------|

### Channel Strategy
| Channel | Tactic | Reach | Cost | Priority |
|---------|--------|-------|------|----------|

### Launch Timeline
| Phase | Timing | Actions | Owner |
|-------|--------|---------|-------|
| Pre-launch | [dates] | [list] | [who] |
| Launch week | [dates] | [list] | [who] |
| Post-launch | [dates] | [list] | [who] |

### Success Metrics
| Metric | 30-day target | 90-day target |
|--------|-------------|-------------|

### Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|

### Expansion Plan
[After beachhead: which adjacent segments, in what order, with what adaptations]
```

Save as markdown.

### Step 6: Offer Next Steps

- "Want me to **design growth loops** for post-launch traction?"
- "Should I **create competitive battlecards** for sales?"
- "Want me to **draft marketing copy** for the launch?"
- "Should I **build a metrics dashboard** for launch tracking?"

## Notes

- "Everyone" is not a segment — the tighter the beachhead, the faster you learn
- The ICP should be specific enough that sales/marketing can identify prospects in 30 seconds
- Messaging should use the customer's language, not your internal terminology
- Pre-launch activities (waitlist, beta, early access) are as important as launch day
- Plan for post-launch: the first 90 days after launch determine long-term trajectory
