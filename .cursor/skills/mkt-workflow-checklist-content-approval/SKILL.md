---
name: mkt-workflow-checklist-content-approval
description: "Content approval workflow for team collaboration. Marketing workflow for Cursor (AgentKits). Use when the user asks for /checklist:content-approval or a full checklist content-approval workflow."
disable-model-invocation: true
---

# Marketing Workflow: checklist/content-approval

> Cursor adaptation of AgentKits `/checklist:content-approval`. Invoke explicitly:
> «Следуй skill mkt-workflow-checklist-content-approval» или `@.cursor/skills/mkt-workflow-checklist-content-approval/SKILL.md`

## Cursor notes

- Slash commands (`/checklist:content-approval`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Prerequisites

Before running this command, ensure you have:
- [ ] Content type defined
- [ ] Team structure known
- [ ] Compliance requirements understood

## Context Loading

Load these files first:
1. `./README.md` - Product context
2. `./docs/brand/` - Brand guidelines
3. `./docs/workflows/` - Existing workflows

---

## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-content-strategy/SKILL.md` and `.cursor/.cursor/skills/mkt-mkt-marketing-fundamentals/SKILL.md`.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Output Scope

**Question:** "What level of approval workflow do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - Simple workflow stages
- **Recommended** - Full workflow with checklists
- **Complete** - Enterprise with escalation
- **Custom** - I'll specify requirements

---

### Step 2: Ask Content Type

**Question:** "What type of content needs approval?"
**Header:** "Content"
**MultiSelect:** false

**Options:**
- **Blog/Article** - Written content
- **Social Post** - Social media content
- **Email** - Email campaigns
- **Landing Page** - Web pages

---

### Step 3: Ask Team Size

**Question:** "What's your team size and structure?"
**Header:** "Team"
**MultiSelect:** false

**Options:**
- **Solo** - Self-review only
- **Small** - 2-3 reviewers
- **Medium** - Multiple roles involved
- **Enterprise** - Full department

---

### Step 4: Ask Compliance Needs

**Question:** "What compliance requirements apply?"
**Header:** "Compliance"
**MultiSelect:** true

**Options:**
- **Brand** - Voice and style
- **SEO** - Search optimization
- **Legal** - Claims and disclaimers
- **Accessibility** - A11y standards

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Content Approval Configuration

| Parameter | Value |
|-----------|-------|
| Content Type | [description] |
| Team Size | [selected team] |
| Compliance | [selected compliance] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Create this approval workflow?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, create workflow** - Start creation
- **No, change settings** - Go back to modify

---

## Workflow

1. **Draft Creation**
   - Creator completes content
   - Self-review checklist
   - Submit for review

2. **Review Process**
   - Content review
   - SEO review
   - Legal review (if needed)
   - Feedback provided

3. **Revisions**
   - Address feedback
   - Update version
   - Request re-review

4. **Approval & Publish**
   - Final sign-off
   - Schedule content
   - Publish and verify

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Content creation | `copywriter` | Draft stage |
| SEO review | `attraction-specialist` | Optimization |
| Quality check | `researcher` | Fact verification |
| Final polish | `copywriter` | Revisions |

---

## Output Format

### Basic Scope

```markdown
## Content Approval Workflow

### Stages
Draft → Review → Revisions → Approval → Publish

### Stage Checklist
**Draft:**
- [ ] Content complete
- [ ] Self-reviewed

**Review:**
- [ ] Feedback provided
- [ ] Revisions requested

**Approval:**
- [ ] Sign-off received
- [ ] Scheduled
```

### Recommended Scope

[Include Basic + Full stage checklists + Reviewer roles + SLA table + Feedback format]

### Complete Scope

[Include all + Escalation process + Quality standards + Content type matrix + Version control]

---

## Workflow Stages

### Stage 1: Draft Creation
- [ ] Brief reviewed and understood
- [ ] Target audience defined
- [ ] Key messages included
- [ ] SEO keywords incorporated
- [ ] CTA clear and compelling
- [ ] Self-review complete

### Stage 2: Review Process
**Content Reviewer:**
- [ ] Accuracy and factual correctness
- [ ] Brand voice consistency
- [ ] Grammar and spelling
- [ ] Logical flow

**SEO Reviewer:**
- [ ] Primary keyword placement
- [ ] Header structure
- [ ] Meta tags optimized

### Stage 3: Revisions
- [ ] Address all "Must Fix" items
- [ ] Consider "Should Fix" suggestions
- [ ] Update version number

### Stage 4: Final Approval
- [ ] All feedback addressed
- [ ] Quality standards met
- [ ] Ready for publication

---

## Content Types & Requirements

| Type | Reviewers | Approval | SLA |
|------|-----------|----------|-----|
| Blog Post | Content + SEO | Marketing Lead | 3 days |
| Social Post | Content | Social Manager | Same day |
| Email | Content + Legal | Email Manager | 2 days |
| Landing Page | Content + SEO + Legal | Marketing Lead | 5 days |

---

## Pre-Delivery Validation

Before delivering approval workflow:
- [ ] All stages defined
- [ ] Reviewer roles assigned
- [ ] SLAs documented
- [ ] Escalation path clear
- [ ] Quality standards included

---

## Output Location

Save workflow to: `./docs/workflows/approval-[content-type]-[YYYY-MM-DD].md`

---

## Next Steps

After approval workflow, consider:
- `mkt-workflow-content-blog` - Create content using workflow
- `mkt-workflow-brand-voice` - Define brand voice guidelines
- `/docs-manager` - Document management
