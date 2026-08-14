---
name: mkt-workflow-pricing-strategy
description: "Design pricing, packaging, and monetization strategy. Marketing workflow for Cursor (AgentKits). Use when the user asks for /pricing:strategy or a full pricing strategy workflow."
disable-model-invocation: true
---

# Marketing Workflow: pricing/strategy

> Cursor adaptation of AgentKits `/pricing:strategy`. Invoke explicitly:
> «Следуй skill mkt-workflow-pricing-strategy» или `@.cursor/skills/mkt-workflow-pricing-strategy/SKILL.md`

## Cursor notes

- Slash commands (`/pricing:strategy`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Prerequisites

Before running this command, ensure you have:
- [ ] Product/service clearly defined
- [ ] Target market identified
- [ ] Competitor pricing researched (or will be)
- [ ] Current pricing structure (if exists)

## Context Loading

Load these files first:
1. `./README.md` - Product context
2. `./docs/personas/` - Target customer profiles
3. `.cursor/.cursor/skills/mkt-mkt-pricing-strategy/SKILL.md` - Pricing frameworks
4. `.cursor/.cursor/skills/mkt-mkt-marketing-psychology/SKILL.md` - Pricing psychology

---

## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-pricing-strategy/SKILL.md` and `.cursor/.cursor/skills/mkt-mkt-marketing-psychology/SKILL.md`.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Output Scope

**Question:** "What level of pricing strategy do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - Pricing structure recommendation
- **Recommended** - Full strategy with packaging
- **Complete** - Comprehensive with implementation
- **Custom** - I'll specify what I need

---

### Step 2: Ask Pricing Challenge

**Question:** "What's your main pricing challenge?"
**Header:** "Challenge"
**MultiSelect:** false

**Options:**
- **New Product** - First-time pricing decision
- **Optimization** - Improve existing pricing
- **Restructure** - Change pricing model
- **Expansion** - Add tiers or plans

---

### Step 3: Ask Value Metric

**Question:** "How do you want to charge?"
**Header:** "Metric"
**MultiSelect:** false

**Options:**
- **Per Seat** - Per user/seat pricing
- **Usage-Based** - Pay for what you use
- **Feature-Based** - Tiers by features
- **Flat Fee** - Single price for all

---

### Step 4: Ask Target Market

**Question:** "Who's your primary market?"
**Header:** "Market"
**MultiSelect:** false

**Options:**
- **SMB** - Small businesses, startups
- **Mid-Market** - Growing companies
- **Enterprise** - Large organizations
- **Consumer** - Individual users

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Pricing Strategy Configuration

| Parameter | Value |
|-----------|-------|
| Product/Challenge | [description] |
| Pricing Challenge | [selected challenge] |
| Value Metric | [selected metric] |
| Target Market | [selected market] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Create this pricing strategy?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, create strategy** - Start analysis
- **No, change settings** - Go back to modify

---

## The Three Pricing Axes

1. **Packaging**: What's included at each tier?
2. **Pricing Metric**: What do you charge for?
3. **Price Point**: How much do you charge?

---

## Value Metrics

| Metric | Best For | Examples |
|--------|----------|----------|
| Per user/seat | Collaboration tools | Slack, Notion |
| Per usage | Variable consumption | AWS, Twilio |
| Per feature | Modular products | HubSpot add-ons |
| Per contact/record | CRM, email tools | Mailchimp |
| Per transaction | Payments | Stripe |
| Flat fee | Simple products | Basecamp |

---

## Workflow

1. **Current State Analysis**
   - Existing pricing structure
   - Competitive positioning
   - Customer feedback
   - Conversion data

2. **Research & Validation**
   - Van Westendorp survey
   - Willingness to pay analysis
   - Competitor benchmarking
   - Feature value ranking

3. **Strategy Design**
   - Value metric selection
   - Tier structure
   - Price point setting
   - Feature packaging

4. **Implementation Planning**
   - Rollout strategy
   - Grandfathering policy
   - Communication plan

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Strategy design | `planner` | Primary task |
| Market research | `researcher` | Competitive analysis |
| Page optimization | `conversion-optimizer` | Pricing page CRO |

---

## Output Format

### Basic Scope

```markdown
## Pricing Strategy: [Product]

### Recommendation
- Value metric: [Metric]
- Tier count: [Number]
- Price anchoring: [Strategy]

### Proposed Tiers
| Tier | Price | Target |
|------|-------|--------|
| [Name] | $[X]/mo | [Target] |

### Rationale
[Why this structure]
```

### Recommended Scope

[Include Basic + Feature packaging + Competitive positioning + Psychology applications + Pricing page recommendations]

### Complete Scope

[Include all + Research methodology + Rollout plan + Grandfathering + Communication templates + A/B testing framework]

---

## Output Location

Save strategy to: `./docs/pricing/strategy-[product]-[YYYY-MM-DD].md`

---

## Pre-Delivery Validation

Before delivering pricing strategy:
- [ ] Value metric aligned with customer value
- [ ] Tier structure supports growth
- [ ] Psychology principles applied
- [ ] Competitive positioning clear
- [ ] Rollout plan included (Complete scope)

---

## Next Steps

After pricing strategy, consider:
- `mkt-workflow-cro-page` - Optimize pricing page
- `mkt-workflow-cro-paywall` - Design upgrade screens
- `mkt-workflow-marketing-psychology` - Apply pricing psychology
