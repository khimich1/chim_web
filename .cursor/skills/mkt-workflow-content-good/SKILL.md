---
name: mkt-workflow-content-good
description: "Write good creative & smart copy [GOOD]. Marketing workflow for Cursor (AgentKits). Use when the user asks for /content:good or a full content good workflow."
disable-model-invocation: true
---

# Marketing Workflow: content/good

> Cursor adaptation of AgentKits `/content:good`. Invoke explicitly:
> «Следуй skill mkt-workflow-content-good» или `@.cursor/skills/mkt-workflow-content-good/SKILL.md`

## Cursor notes

- Slash commands (`/content:good`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-copywriting/SKILL.md`, `.cursor/.cursor/skills/mkt-mkt-content-strategy/SKILL.md`, `.cursor/.cursor/skills/mkt-mkt-marketing-psychology/SKILL.md`.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Output Scope

**Question:** "What level of copy output do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - Quality copy with variations
- **Recommended** - Researched copy with strategy
- **Complete** - Full creative brief + copy + alternatives
- **Custom** - I'll specify what I need

---

### Step 2: Ask Content Type

**Question:** "What type of copy are you creating?"
**Header:** "Type"
**MultiSelect:** false

**Options:**
- **Web Copy** - Landing pages, homepage, product
- **Marketing Materials** - Ads, emails, campaigns
- **Long-form Content** - Blog, articles, guides
- **Brand Copy** - Taglines, mission, messaging

---

### Step 3: Ask Target Audience

**Question:** "Who is the target audience?"
**Header:** "Audience"
**MultiSelect:** false

**Options:**
- **B2B Professionals** - Business decision makers
- **B2C Consumers** - General consumers
- **Technical Users** - Developers, IT, specialists
- **Mixed/Unknown** - Need to research

---

### Step 4: Ask Tone & Voice

**Question:** "What tone should the copy have?"
**Header:** "Tone"
**MultiSelect:** false

**Options:**
- **Professional** - Authoritative, trustworthy
- **Conversational** - Friendly, approachable
- **Bold/Provocative** - Challenging, disruptive
- **Empathetic** - Understanding, supportive

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Good Copy Configuration

| Parameter | Value |
|-----------|-------|
| Request | [user request summary] |
| Type | [selected type] |
| Audience | [selected audience] |
| Tone | [selected tone] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Create quality copy?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, create copy** - Start researched creation
- **No, change settings** - Go back to modify

---

## Workflow

1. **Research Phase**
   - If screenshot: Use multimodal analysis
   - If video: Extract key context
   - Use `researcher` agents to gather info
   - Search codebase if needed

2. **Planning Phase**
   - Use `planner` agent to structure
   - Define messaging strategy
   - Outline key points

3. **Creation Phase**
   - Use `copywriter` agent
   - Apply brand voice
   - Create multiple variations

4. **Quality Check**
   - Review against objectives
   - Ensure audience fit

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Research | `researcher` | Context gathering |
| Planning | `planner` | Strategy development |
| Copy creation | `copywriter` | Primary output |
| Voice check | `brand-voice-guardian` | Brand alignment |

---

## Output Format

### Basic Scope

```markdown
## [Content Type]: [Brief Description]

### Primary Version
[Quality copy]

### Alternative 1
[Variation]

### Alternative 2
[Variation]
```

### Recommended Scope

[Include Basic + Research insights + Strategy rationale + Audience notes]

### Complete Scope

[Include all + Creative brief + Multiple formats + Implementation guide]

---

## Output Location

Save good copy to: `./docs/content/good/[type]-[YYYY-MM-DD].md`

---

## Note

For quick copy without research, use `mkt-workflow-content-fast` instead.
