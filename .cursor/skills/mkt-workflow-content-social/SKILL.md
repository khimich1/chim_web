---
name: mkt-workflow-content-social
description: "Create platform-specific social content. Marketing workflow for Cursor (AgentKits). Use when the user asks for /content:social or a full content social workflow."
disable-model-invocation: true
---

# Marketing Workflow: content/social

> Cursor adaptation of AgentKits `/content:social`. Invoke explicitly:
> «Следуй skill mkt-workflow-content-social» или `@.cursor/skills/mkt-workflow-content-social/SKILL.md`

## Cursor notes

- Slash commands (`/content:social`) недоступны — используй этот workflow skill.
- Atomic skills: `.cursor/skills/mkt-*/SKILL.md` (префикс `mkt-`, не путать с PM skills).
- Personas: `.cursor/rules/agents/mkt-*.md`
- Контекст проекта: `docs/marketing/brand-context.md`, `docs/strategy/seo-strategy.md`
- Сохраняй артефакты в `docs/marketing/` (campaigns/, research/, content/, plans/)
- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры

---


## Prerequisites

Before running this command, ensure:
- [ ] Topic or message to share is clear
- [ ] Target platform(s) identified
- [ ] Any links or assets referenced are ready

---

## Context Loading (Execute First)

Load context in this order:
1. **Project**: Read `./README.md` for product context
2. **Brand**: Read `docs/marketing/brand-context.md` for voice
3. **Social Skill**: Load `.cursor/.cursor/skills/mkt-mkt-social-media/SKILL.md`
4. **Playbook**: Load `.claude/skills/social-media/references/social-media-playbook.md`
5. **Prior Posts**: Check `./docs/content/social/` for consistency

---

## Language & Quality Standards

**CRITICAL**: Respond in the same language the user is using. If Vietnamese, respond in Vietnamese. If Spanish, respond in Spanish.

**Standards**: Token efficiency, sacrifice grammar for concision, list unresolved questions at end.

**Skills**: Read `.cursor/.cursor/skills/mkt-mkt-social-media/SKILL.md` and `.cursor/.cursor/skills/mkt-mkt-copywriting/SKILL.md`.

**Components**: Reference `./.claude/components/interactive-questions.md`

---

## Interactive Parameter Collection

### Step 1: Ask Output Scope

**Question:** "What level of social content do you need?"
**Header:** "Scope"
**MultiSelect:** false

**Options:**
- **Basic** - Single post with variations
- **Recommended** - Multi-format content package
- **Complete** - Full campaign with calendar
- **Custom** - I'll select specific deliverables

---

### Step 2: Ask Platform

**Question:** "Which platform(s) are you posting to?"
**Header:** "Platform"
**MultiSelect:** true

**Options:**
- **LinkedIn** - B2B, professional, long-form
- **Twitter/X** - Real-time, threads, engagement
- **Instagram** - Visual, reels, stories
- **TikTok** - Short video, trends, entertainment

---

### Step 3: Ask Content Goal

**Question:** "What's the primary goal of this content?"
**Header:** "Goal"
**MultiSelect:** false

**Options:**
- **Engagement** - Likes, comments, shares
- **Traffic** - Drive to website/landing page
- **Brand Awareness** - Visibility, reach
- **Lead Generation** - Capture leads, signups

---

### Step 4: Ask Content Type

**Question:** "What type of content?"
**Header:** "Format"
**MultiSelect:** false

**Options:**
- **Educational** - Tips, how-tos, insights
- **Promotional** - Product, offer, announcement
- **Storytelling** - Case study, behind-scenes
- **Engagement** - Polls, questions, trends

---

### Step 5: Confirmation

**Display summary:**

```markdown
## Social Content Configuration

| Parameter | Value |
|-----------|-------|
| Topic | [topic description] |
| Platform(s) | [selected platforms] |
| Goal | [selected goal] |
| Content Type | [selected type] |
| Scope | [Basic/Recommended/Complete] |
```

**Question:** "Create social content?"
**Header:** "Confirm"
**MultiSelect:** false

**Options:**
- **Yes, create content** - Start content creation
- **No, change settings** - Go back to modify

---

## Platform Specifications

| Platform | Format | Copy Length | Hashtags |
|----------|--------|-------------|----------|
| LinkedIn | Long-form, document | 1-3k chars | 3-5 |
| Twitter/X | Thread, visual | 280 chars/tweet | 1-2 |
| Instagram | Reel, carousel | 125-150 chars | 20-30 |
| TikTok | Short video | 150 chars | 3-5 |

---

## Workflow

1. **Platform Analysis**
   - Format requirements
   - Algorithm preferences
   - Best practices

2. **Content Adaptation**
   - Platform-native format
   - Copy style
   - Hashtag strategy

3. **Engagement Optimization**
   - Hook optimization
   - CTA placement
   - Reply strategy

4. **Variant Creation**
   - Multiple hooks
   - Different angles
   - A/B versions

---

## Agent Delegation

| Task | Agent | Trigger |
|------|-------|---------|
| Social copy | `copywriter` | Content creation |
| Platform strategy | `brainstormer` | Format optimization |
| Engagement tactics | `planner` | Campaign planning |

---

## Output Format

### Basic Scope

```markdown
## [Platform] Post

**Hook:** [First line that stops scroll]

**Body:**
[Main content]

**CTA:** [What you want them to do]

**Hashtags:** #tag1 #tag2 #tag3

**Visual:** [Image/video description]
```

### Recommended Scope

[Include Basic + Platform variations + Visual specs + Posting recommendations]

### Complete Scope

[Include all + Content calendar + Engagement strategy + Performance tracking plan]

---

## Output Location

Save social content to: `./docs/content/social/[platform]-[topic]-[YYYY-MM-DD].md`

---

## Pre-Delivery Validation

Before delivering social content:

- [ ] **Hook Strong**: First line stops the scroll
- [ ] **Platform Native**: Format fits platform norms
- [ ] **Character Count**: Within platform limits
- [ ] **Hashtags Appropriate**: Quantity matches platform
- [ ] **CTA Present**: Clear desired action
- [ ] **Visual Specified**: Image/video description included
- [ ] **Links Checked**: Any URLs are correct
- [ ] **Brand Voice**: Matches guidelines

---

## Next Steps After Delivery

1. **Review**: Approve content and visuals
2. **Create Assets**: Design images/videos if needed
3. **Schedule**: Run `mkt-workflow-social-schedule` for timing
4. **Post**: Publish to platforms
5. **Engage**: Monitor and respond to comments
6. **Analyze**: Track engagement metrics
7. **Repurpose**: Adapt top performers for other platforms
