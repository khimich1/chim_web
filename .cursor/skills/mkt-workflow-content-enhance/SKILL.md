---
name: mkt-workflow-content-enhance
description: "Analyze the current copy issues and enhance it. Marketing workflow for Cursor (AgentKits). Use when the user asks for /content:enhance or a full content enhance workflow."
disable-model-invocation: true
---

# Marketing Workflow: content/enhance

> Cursor adaptation of AgentKits `/content:enhance`. Invoke explicitly:
> «Следуй skill mkt-workflow-content-enhance» или `@.cursor/skills/mkt-workflow-content-enhance/SKILL.md`

## Cursor notes

- Slash commands (`/content:enhance`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-copywriting/SKILL.md`, `.cursor/.cursor/skills/mkt-mkt-marketing-psychology/SKILL.md`, `.cursor/.cursor/skills/mkt-mkt-content-strategy/SKILL.md`.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Enhancement Scope

**Question:** "What level of enhancement do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - Quick fixes and polish
- **Recommended** - Full enhancement with alternatives
- **Complete** - Deep rewrite with multiple versions
- **Custom** - I'll specify enhancement areas

---

### Step 2: Ask Content Type

**Question:** "What type of content are you enhancing?"
**Header:** "Type"
**MultiSelect:** false

**Options:**
- **Web Copy** - Landing pages, homepage, product pages
- **Marketing Copy** - Ads, emails, social posts
- **Long-form** - Blog posts, articles, guides
- **Short-form** - Headlines, taglines, CTAs

---

### Step 3: Ask Enhancement Focus

**Question:** "What should we focus on improving?"
**Header:** "Focus"
**MultiSelect:** true

**Options:**
- **Clarity** - Simpler, easier to understand
- **Persuasion** - More compelling, action-driving
- **Concision** - Shorter, tighter, no fluff
- **Tone/Voice** - Brand alignment, consistency

---

### Step 4: Ask Output Preference

**Question:** "What output format do you prefer?"
**Header:** "Output"
**MultiSelect:** false

**Options:**
- **Enhanced Only** - Final improved version
- **Comparison** - Before and after side-by-side
- **Alternatives** - Multiple enhanced versions
- **Annotated** - Changes with explanations

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Content Enhancement Configuration

| Parameter | Value |
|-----------|-------|
| Content | [description or URL] |
| Type | [selected type] |
| Focus Areas | [selected areas] |
| Output Format | [selected format] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Enhance this content?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, enhance** - Start enhancement
- **No, change settings** - Go back to modify

---

## Workflow

1. **Content Analysis**
   - If URL: Use WebFetch to retrieve
   - If screenshot: Use multimodal analysis
   - Identify issues and opportunities
   - Document current state

2. **Issue Diagnosis**
   - Identify weak spots
   - Note missing elements
   - Assess conversion potential
   - Check brand alignment

3. **Enhancement Process**
   - Apply focus area improvements
   - Maintain original intent
   - Preserve key messages
   - Strengthen weak areas

4. **Output Delivery**
   - Enhanced version
   - Before/after comparison
   - Explanation of changes
   - Improvement metrics

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Copy enhancement | `copywriter` | Primary task |
| Brand review | `brand-voice-guardian` | Tone consistency |
| CRO check | `conversion-optimizer` | Conversion elements |
| Psychology review | `brainstormer` | Persuasion elements |

---

## Output Format

### Basic Scope

```markdown
# Content Enhancement

## Enhanced Version
[Improved content]

## Key Changes
- [Change 1]: [Reason]
- [Change 2]: [Reason]
```

### Recommended Scope

[Include Basic + Before/after comparison + Alternative versions + Improvement metrics]

### Complete Scope

[Include all + Multiple rewrites + A/B test suggestions + Style guide notes + Conversion analysis]

---

## Output Location

Save enhancement to: `./docs/content/enhanced/[content-name]-[YYYY-MM-DD].md`
