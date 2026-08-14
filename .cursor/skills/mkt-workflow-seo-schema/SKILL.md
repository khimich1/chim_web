---
name: mkt-workflow-seo-schema
description: "Add or optimize schema markup and structured data. Marketing workflow for Cursor (AgentKits). Use when the user asks for /seo:schema or a full seo schema workflow."
disable-model-invocation: true
---

# Marketing Workflow: seo/schema

> Cursor adaptation of AgentKits `/seo:schema`. Invoke explicitly:
> «Следуй skill mkt-workflow-seo-schema» или `@.cursor/skills/mkt-workflow-seo-schema/SKILL.md`

## Cursor notes

- Slash commands (`/seo:schema`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Prerequisites

Before running this command, ensure you have:
- [ ] Page type or URL identified
- [ ] Current schema status known
- [ ] Rich result goals defined

## Context Loading

Load these files first:
1. `./README.md` - Product context
2. `./docs/seo/` - Existing SEO research
3. `.cursor/.cursor/skills/mkt-mkt-schema-markup/SKILL.md` - Schema frameworks

---

## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-schema-markup/SKILL.md` and `.cursor/.cursor/skills/mkt-mkt-seo-mastery/SKILL.md`.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Output Scope

**Question:** "What level of schema markup do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - Single schema type
- **Recommended** - Multiple schemas with validation
- **Complete** - Full implementation with testing
- **Custom** - I'll specify requirements

---

### Step 2: Ask Page Type

**Question:** "What type of page needs schema markup?"
**Header:** "Page"
**MultiSelect:** false

**Options:**
- **Article/Blog** - Content pages
- **Product/Service** - E-commerce, SaaS
- **Local Business** - Physical locations
- **Organization** - Company pages

---

### Step 3: Ask Schema Types

**Question:** "Which schema types do you need?"
**Header:** "Schema"
**MultiSelect:** true

**Options:**
- **FAQ** - FAQ sections for rich snippets
- **HowTo** - Step-by-step instructions
- **Review/Rating** - Star ratings display
- **Breadcrumb** - Navigation structure

---

### Step 4: Ask Current State

**Question:** "What's your current schema status?"
**Header:** "Status"
**MultiSelect:** false

**Options:**
- **No Schema** - Starting fresh
- **Basic Schema** - Some markup exists
- **Has Errors** - Validation issues
- **Optimizing** - Enhancing existing

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Schema Markup Configuration

| Parameter | Value |
|-----------|-------|
| Page | [page description] |
| Page Type | [selected type] |
| Schema Types | [selected schemas] |
| Current Status | [selected status] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Create schema markup?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, create schema** - Start schema work
- **No, change settings** - Go back to modify

---

## Common Schema Types

| Schema Type | Use For | Rich Result |
|-------------|---------|-------------|
| Article | Blog posts, news | Article cards |
| Product | E-commerce, SaaS | Product info, reviews |
| FAQ | FAQ sections | Expandable FAQ |
| HowTo | Tutorials, guides | Step cards |
| Organization | Company info | Knowledge panel |
| LocalBusiness | Local services | Maps, info |
| Review/Rating | Reviews | Star ratings |
| Breadcrumb | Navigation | Breadcrumb trail |
| Video | Video content | Video thumbnails |
| Event | Events, webinars | Event listings |
| Person | About pages | Knowledge panel |
| SoftwareApplication | Apps, tools | App info |

---

## Workflow

1. **Page Type Analysis**
   - Identify page purpose
   - Determine applicable schema types
   - Check current markup (if any)

2. **Schema Generation**
   - Use JSON-LD format (preferred)
   - Include required properties
   - Add recommended properties
   - Validate with tools

3. **Rich Result Eligibility**
   - Check if page qualifies
   - Meet content guidelines
   - Ensure accuracy

4. **Testing & Validation**
   - Google Rich Results Test
   - Schema.org validator
   - Search Console monitoring

---

## JSON-LD Best Practices

1. **Place in `<head>`**: Cleaner, easier to manage
2. **One script per type**: Or combine related types
3. **Match visible content**: Schema must reflect page content
4. **Keep updated**: Especially prices, dates, availability

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Schema creation | `seo-specialist` | Primary task |
| Content analysis | `copywriter` | Property values |
| Technical review | `attraction-specialist` | Implementation |

---

## Output Format

### Basic Scope

```markdown
## Schema Markup: [Page Type]

### JSON-LD Code
```json
{
  "@context": "https://schema.org",
  "@type": "[Type]",
  ...
}
```

### Placement
[Where to add in HTML]
```

### Recommended Scope

[Include Basic + Multiple schema types + Property explanations + Validation results + Rich result preview]

### Complete Scope

[Include all + All applicable schemas + Testing checklist + Implementation guide + Monitoring setup + Error handling]

---

## Validation Checklist

- [ ] Required properties included
- [ ] Recommended properties added
- [ ] Validated with testing tool
- [ ] No errors or warnings
- [ ] Content matches visible page

---

## Pre-Delivery Validation

Before delivering schema markup:
- [ ] JSON-LD syntax valid
- [ ] Required properties included
- [ ] Content matches visible page
- [ ] Tested with validation tools
- [ ] Implementation instructions clear

---

## Output Location

Save schema to: `./docs/seo/schema-[page-type]-[YYYY-MM-DD].md`

---

## Next Steps

After schema markup, consider:
- `mkt-workflow-seo-audit` - Full SEO audit
- `mkt-workflow-seo-optimize` - On-page optimization
- `mkt-workflow-cro-page` - Conversion optimization
