---
name: mkt-workflow-sales-battlecard
description: "Create competitive battlecard. Marketing workflow for Cursor (AgentKits). Use when the user asks for /sales:battlecard or a full sales battlecard workflow."
disable-model-invocation: true
---

# Marketing Workflow: sales/battlecard

> Cursor adaptation of AgentKits `/sales:battlecard`. Invoke explicitly:
> «Следуй skill mkt-workflow-sales-battlecard» или `@.cursor/skills/mkt-workflow-sales-battlecard/SKILL.md`

## Cursor notes

- Slash commands (`/sales:battlecard`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Prerequisites

Before running this command, ensure you have:
- [ ] Competitor clearly identified (name, URL, product)
- [ ] Your product positioning defined
- [ ] Sales scenarios identified

## Context Loading

Load these files first:
1. `./README.md` - Product context
2. `./docs/personas/` - Target buyer profiles
3. `.cursor/.cursor/skills/mkt-mkt-competitor-alternatives/SKILL.md` - Competitive frameworks

---

## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-marketing-fundamentals/SKILL.md` and `.cursor/.cursor/skills/mkt-mkt-competitor-alternatives/SKILL.md`.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Output Scope

**Question:** "What level of battlecard do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - Quick comparison and key talking points
- **Recommended** - Full battlecard with objection handling
- **Complete** - Comprehensive with win/loss analysis
- **Custom** - I'll specify focus areas

---

### Step 2: Ask Competitor Type

**Question:** "What type of competitor is this?"
**Header:** "Type"
**MultiSelect:** false

**Options:**
- **Direct Competitor** - Same product category
- **Indirect Competitor** - Alternative solution
- **Emerging Threat** - New market entrant
- **Market Leader** - Dominant player

---

### Step 3: Ask Focus Areas

**Question:** "Which areas should we emphasize?"
**Header:** "Focus"
**MultiSelect:** true

**Options:**
- **Pricing** - Cost comparison and value
- **Features** - Capability differences
- **Support** - Service and implementation
- **Integration** - Technical compatibility

---

### Step 4: Ask Sales Context

**Question:** "What's the primary sales scenario?"
**Header:** "Context"
**MultiSelect:** false

**Options:**
- **New Prospect** - First-time competitive encounter
- **Competitive Deal** - Active head-to-head
- **Win-Back** - Lost customer recovery
- **Replacement** - Switching from competitor

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Battlecard Configuration

| Parameter | Value |
|-----------|-------|
| Competitor | [competitor name] |
| Type | [selected type] |
| Focus Areas | [selected areas] |
| Sales Context | [selected context] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Create this battlecard?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, create battlecard** - Start creation
- **No, change settings** - Go back to modify

---

## Workflow

1. **Competitor Research**
   - Product features and pricing
   - Target market and positioning
   - Strengths and weaknesses
   - Customer reviews and complaints
   - Recent news and updates

2. **Comparison Analysis**
   - Side-by-side comparison
   - Win/loss scenarios
   - Differentiators

3. **Sales Enablement**
   - Objection handling scripts
   - Trap questions
   - Customer proof points

4. **Format for Use**
   - Easy-to-scan layout
   - Mobile-friendly version
   - Quick reference card

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Competitor research | `researcher` | Data gathering |
| Battlecard creation | `sales-enabler` | Primary task |
| Copy polish | `copywriter` | Talk tracks |

---

## Output Format

### Basic Scope

```markdown
## Battlecard: [Competitor]

### Quick Comparison
| Aspect | Us | Them |
|--------|-----|------|
| [Key area] | [Our position] | [Their position] |

### Key Differentiators
- [Differentiator 1]
- [Differentiator 2]

### Top Objection Responses
**"[Objection]"**
> [Response]
```

### Recommended Scope

[Include Basic + Full strengths/weaknesses + Win/loss scenarios + Trap questions + Customer quotes]

### Complete Scope

[Include all + Detailed feature comparison + Competitive positioning + Sales playbook + Training materials]

---

## Pre-Delivery Validation

Before delivering battlecard:
- [ ] All claims factually accurate
- [ ] Objection responses tested
- [ ] Differentiation points clear
- [ ] Sales scenarios covered
- [ ] Easy to scan in sales situation

---

## Output Location

Save battlecard to: `./docs/sales/battlecard-[competitor]-[YYYY-MM-DD].md`

---

## Next Steps

After battlecard creation, consider:
- `mkt-workflow-sales-pitch` - Create prospect-specific pitch
- `mkt-workflow-sales-outreach` - Generate outreach sequence
- `mkt-workflow-competitor-deep` - Deep competitor analysis
