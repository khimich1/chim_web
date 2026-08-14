---
name: mkt-workflow-checklist-seo-weekly
description: "Weekly SEO maintenance and optimization checklist. Marketing workflow for Cursor (AgentKits). Use when the user asks for /checklist:seo-weekly or a full checklist seo-weekly workflow."
disable-model-invocation: true
---

# Marketing Workflow: checklist/seo-weekly

> Cursor adaptation of AgentKits `/checklist:seo-weekly`. Invoke explicitly:
> «Следуй skill mkt-workflow-checklist-seo-weekly» или `@.cursor/skills/mkt-workflow-checklist-seo-weekly/SKILL.md`

## Cursor notes

- Slash commands (`/checklist:seo-weekly`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Prerequisites

Before running this command, ensure you have:
- [ ] Website or domain identified
- [ ] Access to SEO tools
- [ ] MCP configured: `google-search-console`, `semrush` (optional)

## Context Loading

Load these files first:
1. `./README.md` - Product context
2. `./docs/seo/` - Previous SEO work
3. `.cursor/.cursor/skills/mkt-mkt-seo-mastery/SKILL.md` - SEO frameworks

---

## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-seo-mastery/SKILL.md` and `.cursor/.cursor/skills/mkt-mkt-marketing-fundamentals/SKILL.md`.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Output Scope

**Question:** "What level of SEO checklist do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - Essential weekly checks
- **Recommended** - Full weekly review
- **Complete** - Comprehensive with reporting
- **Custom** - I'll specify focus areas

---

### Step 2: Ask SEO Focus

**Question:** "Which SEO areas need attention?"
**Header:** "Focus"
**MultiSelect:** true

**Options:**
- **Rankings** - Position tracking
- **Technical** - Crawl, indexing, speed
- **Content** - Optimization, updates
- **Links** - Backlinks, internal links

---

### Step 3: Ask Site Size

**Question:** "What's the size of your site?"
**Header:** "Size"
**MultiSelect:** false

**Options:**
- **Small** - Under 50 pages
- **Medium** - 50-500 pages
- **Large** - 500+ pages
- **Enterprise** - Multi-site

---

### Step 4: Ask Reporting Needs

**Question:** "What reporting is needed?"
**Header:** "Reporting"
**MultiSelect:** false

**Options:**
- **Personal** - Internal tracking only
- **Team** - Weekly team updates
- **Client** - Client-ready reports
- **Executive** - Leadership summary

---

### Step 5: Confirmation

**Display summary:**

```markdown
## SEO Weekly Configuration

| Parameter | Value |
|-----------|-------|
| Website | [description] |
| Focus Areas | [selected focus] |
| Site Size | [selected size] |
| Reporting | [selected reporting] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Create this SEO checklist?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, create checklist** - Start creation
- **No, change settings** - Go back to modify

---

## Workflow

1. **Monday: Performance Review**
   - Rankings check
   - Search Console review
   - Traffic analysis

2. **Tuesday: Technical Health**
   - Crawl errors
   - Site health audit
   - Core Web Vitals

3. **Wednesday: Content Optimization**
   - Content audit
   - On-page updates
   - Featured snippets

4. **Thursday: Link Building**
   - Backlink monitoring
   - Outreach pipeline
   - Internal linking

5. **Friday: Competitor & Reporting**
   - Competitor check
   - Keyword research
   - Weekly reporting

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Keyword research | `attraction-specialist` | Content planning |
| Technical audit | `attraction-specialist` | Site health |
| Content gaps | `researcher` | Competitor analysis |
| Performance analysis | `researcher` | Rankings review |

---

## Output Format

### Basic Scope

```markdown
## SEO Weekly: Week of [Date]

### Rankings Check
- [ ] Export current rankings
- [ ] Note changes (+/- 5 positions)
- [ ] Investigate drops

### Technical Check
- [ ] Review crawl errors
- [ ] Check site speed
- [ ] Verify indexing

### Content Actions
- [ ] Optimize 1-2 pages
- [ ] Update outdated content
```

### Recommended Scope

[Include Basic + Full daily breakdown + Metrics dashboard + Quick wins tracker + Tools checklist]

### Complete Scope

[Include all + SEO health scorecard + Link building pipeline + Competitor monitoring + Weekly reporting template]

---

## Weekly Schedule

### Monday: Rankings & Performance
- [ ] Search Console review (clicks, impressions, CTR)
- [ ] Rankings tracker snapshot
- [ ] Analytics organic traffic trend

### Tuesday: Technical Health
- [ ] Check Coverage report
- [ ] Review crawl errors
- [ ] Core Web Vitals check

### Wednesday: Content Optimization
- [ ] Identify underperforming content
- [ ] Optimize 1-2 pages
- [ ] Featured snippet opportunities

### Thursday: Link Building
- [ ] Check new/lost backlinks
- [ ] Send 3-5 outreach emails
- [ ] Internal linking updates

### Friday: Competitor & Reporting
- [ ] Competitor rankings check
- [ ] Research new keyword opportunities
- [ ] Compile weekly metrics

---

## Weekly Metrics Dashboard

| Metric | This Week | Last Week | Change | Target |
|--------|-----------|-----------|--------|--------|
| Organic Sessions | | | | |
| Avg Position | | | | |
| CTR | | | | |
| Keywords in Top 10 | | | | |
| New Backlinks | | | | |

---

## Pre-Delivery Validation

Before delivering SEO checklist:
- [ ] All daily tasks included
- [ ] Metrics dashboard ready
- [ ] Tool requirements listed
- [ ] Reporting needs addressed
- [ ] Weekly schedule complete

---

## Output Location

Save checklist to: `./docs/seo/weekly-[week]-[YYYY-MM-DD].md`

---

## Next Steps

After SEO weekly checklist, consider:
- `mkt-workflow-seo-audit` - Comprehensive SEO audit
- `mkt-workflow-seo-keywords` - Keyword research
- `mkt-workflow-seo-optimize` - Content optimization
