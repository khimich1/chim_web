---
name: mkt-workflow-competitor-alternatives
description: "Create competitor comparison or alternative pages for SEO and sales. Marketing workflow for Cursor (AgentKits). Use when the user asks for /competitor:alternatives or a full competitor alternatives workflow."
disable-model-invocation: true
---

# Marketing Workflow: competitor/alternatives

> Cursor adaptation of AgentKits `/competitor:alternatives`. Invoke explicitly:
> «Следуй skill mkt-workflow-competitor-alternatives» или `@.cursor/skills/mkt-workflow-competitor-alternatives/SKILL.md`

## Cursor notes

- Slash commands (`/competitor:alternatives`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Prerequisites

Before running this command, ensure you have:
- [ ] Competitor name or product to compare
- [ ] Your product positioning defined
- [ ] `mkt-workflow-competitor-deep` analysis completed (recommended)

## Context Loading

Load these files first:
1. `./README.md` - Your product context
2. `./docs/competitors/` - Existing competitor research
3. `.cursor/.cursor/skills/mkt-mkt-competitor-alternatives/SKILL.md` - Page frameworks
4. `.cursor/.cursor/skills/mkt-mkt-seo-mastery/SKILL.md` - SEO optimization

---

## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-competitor-alternatives/SKILL.md`, `.cursor/.cursor/skills/mkt-mkt-seo-mastery/SKILL.md`, `.cursor/.cursor/skills/mkt-mkt-copywriting/SKILL.md`.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Output Scope

**Question:** "What level of alternatives page do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - Page outline and key points
- **Recommended** - Full page with copy
- **Complete** - SEO-optimized with schema
- **Custom** - I'll specify what I need

---

### Step 2: Ask Page Type

**Question:** "What type of alternatives page?"
**Header:** "Type"
**MultiSelect:** false

**Options:**
- **Singular** - "[Product]: Best [Competitor] Alternative"
- **Plural** - "Best [Competitor] Alternatives in 2024"
- **Vs Page** - "[Your Product] vs [Competitor]"
- **Head-to-Head** - "[Competitor A] vs [Competitor B]"

---

### Step 3: Ask Content Depth

**Question:** "How detailed should the comparison be?"
**Header:** "Depth"
**MultiSelect:** false

**Options:**
- **Overview** - High-level comparison
- **Detailed** - Feature-by-feature analysis
- **Comprehensive** - Full research with use cases
- **Authority** - Industry expert perspective

---

### Step 4: Ask SEO Priority

**Question:** "What's the SEO priority?"
**Header:** "SEO"
**MultiSelect:** false

**Options:**
- **Standard** - Basic optimization
- **Competitive** - Target ranking keywords
- **Aggressive** - Full schema and linking
- **Programmatic** - Template for scale

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Alternatives Page Configuration

| Parameter | Value |
|-----------|-------|
| Competitor/Product | [description] |
| Page Type | [selected type] |
| Content Depth | [selected depth] |
| SEO Priority | [selected seo] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Create this alternatives page?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, create page** - Start creation
- **No, change settings** - Go back to modify

---

## Workflow

1. **Research Phase**
   - Competitor product features
   - Pricing structure
   - Common complaints
   - Strengths to acknowledge

2. **Page Structure**
   - Hook and intro
   - Comparison table
   - Feature breakdown
   - Use case recommendations

3. **SEO Optimization**
   - Title and meta tags
   - Schema markup
   - Internal linking
   - Content structure

4. **Copy Creation**
   - Headlines
   - Comparison copy
   - CTAs

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Competitor research | `researcher` | Data gathering |
| Page copy | `copywriter` | Primary task |
| SEO optimization | `seo-specialist` | Complete scope |

---

## Output Format

### Basic Scope

```markdown
## [Page Title]

### Page Strategy
- Type: [Page type]
- URL: /[url-slug]/
- Target Keywords: [List]

### Outline
1. [Section 1]
2. [Section 2]
3. Comparison Table
4. CTA

### Key Messages
- [Message 1]
- [Message 2]
```

### Recommended Scope

[Include Basic + Full page copy + Comparison table + Feature breakdown + SEO elements]

### Complete Scope

[Include all + Schema markup + FAQ section + Internal linking plan + Headline variants]

---

## Output Location

Save page to: `./docs/content/alternatives-[competitor]-[YYYY-MM-DD].md`

---

## Pre-Delivery Validation

Before delivering alternatives page:
- [ ] Comparison is fair and accurate
- [ ] SEO elements optimized (title, meta, headings)
- [ ] Schema markup included (Complete scope)
- [ ] CTAs strategically placed
- [ ] Copy follows brand voice

---

## Next Steps

After alternatives page, consider:
- `mkt-workflow-seo-schema` - Add rich snippet markup
- `mkt-workflow-content-cro` - Optimize for conversion
- `mkt-workflow-seo-keywords` - Find more comparison keywords
