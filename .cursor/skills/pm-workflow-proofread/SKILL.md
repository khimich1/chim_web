---
name: pm-workflow-proofread
description: "Check grammar, logic, and flow in any text — targeted fixes without rewriting. End-to-end PM workflow for Cursor (chains multiple pm skills). Use when the user asks for /proofread or a full proofread workflow."
disable-model-invocation: true
---

# PM Workflow: proofread

> Cursor adaptation of Claude Code `/proofread`. Invoke explicitly:
> «Следуй skill pm-workflow-proofread» или `@.cursor/skills/pm-workflow-proofread/SKILL.md`

## Cursor notes

- Slash commands (`/proofread`) недоступны — используй этот workflow skill.
- Шаги со ссылкой на **skill-name** → прочитай `.cursor/skills/<skill-name>/SKILL.md` и следуй ему.
- Сохраняй артефакты в `docs/pm/` или корень workspace, если пользователь не указал путь.
- После завершения предложи следующий workflow из секции «Next steps» исходной команды.

---


# /proofread -- Grammar & Flow Check

Identify grammar, logical, and flow errors in text. Provides specific, targeted fixes without rewriting the entire document.

## Invocation

```
/proofread [paste text]
/proofread [upload a document]
```

## Workflow

### Step 1: Accept Text

Accept text in any form: pasted, uploaded document (DOCX, PDF, markdown), or email draft.

### Step 2: Analyze

Read and follow `.cursor/skills/grammar-check/SKILL.md`:

Scan for three categories of issues:

**Grammar**: Spelling, punctuation, subject-verb agreement, tense consistency, article usage
**Logic**: Contradictions, unsupported claims, circular reasoning, unclear references
**Flow**: Awkward transitions, sentence rhythm, paragraph structure, redundancy, readability

### Step 3: Report Issues

```
## Proofread Report

**Text length**: [word count]
**Issues found**: [count by category]

### Issues

#### 1. [Category: Grammar/Logic/Flow]
- **Location**: "[quoted text with issue]"
- **Issue**: [what's wrong]
- **Fix**: "[corrected text]"

[Repeat for each issue]

### Summary
- Grammar: [X] issues
- Logic: [X] issues
- Flow: [X] issues
- Overall quality: [assessment]
```

### Step 4: Offer

- "Want me to **apply all fixes** and return the cleaned text?"
- "Should I **focus on a specific section** in more detail?"

## Notes

- Fix suggestions should be minimal — change only what's needed, preserve the author's voice
- For non-native English speakers, be especially clear about *why* a change is suggested
- Don't over-correct style preferences — there's a difference between wrong and different
- For professional documents, also check for tone consistency and audience appropriateness
