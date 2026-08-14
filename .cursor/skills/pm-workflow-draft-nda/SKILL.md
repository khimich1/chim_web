---
name: pm-workflow-draft-nda
description: "Draft a Non-Disclosure Agreement between two parties with jurisdiction-appropriate clauses. End-to-end PM workflow for Cursor (chains multiple pm skills). Use when the user asks for /draft-nda or a full draft-nda workflow."
disable-model-invocation: true
---

# PM Workflow: draft-nda

> Cursor adaptation of Claude Code `/draft-nda`. Invoke explicitly:
> «Следуй skill pm-workflow-draft-nda» или `@.cursor/skills/pm-workflow-draft-nda/SKILL.md`

## Cursor notes

- Slash commands (`/draft-nda`) недоступны — используй этот workflow skill.
- Шаги со ссылкой на **skill-name** → прочитай `.cursor/skills/<skill-name>/SKILL.md` и следуй ему.
- Сохраняй артефакты в `docs/pm/` или корень workspace, если пользователь не указал путь.
- После завершения предложи следующий workflow из секции «Next steps» исходной команды.

---


# /draft-nda -- NDA Drafting

Draft a professional Non-Disclosure Agreement customized to your situation. Covers information types, jurisdiction, term, and clearly marks clauses that need legal review.

## Invocation

```
/draft-nda Mutual NDA between our startup and a potential enterprise customer
/draft-nda One-way NDA for a freelance contractor accessing our codebase
```

## Workflow

### Step 1: Gather Context

Ask:
- Who are the parties? (company names and roles)
- Mutual or one-way NDA?
- What information is being protected? (trade secrets, code, business data, customer data)
- Jurisdiction? (state/country for governing law)
- Duration? (how long should confidentiality last)
- Any specific concerns? (non-compete, non-solicit, IP ownership)

### Step 2: Draft the NDA

Read and follow `.cursor/skills/draft-nda/SKILL.md`:

Generate a complete NDA covering:
- Parties and recitals
- Definition of confidential information (with specific examples)
- Obligations of the receiving party
- Exclusions (public knowledge, independent development, etc.)
- Term and survival
- Return/destruction of materials
- Remedies
- Governing law and jurisdiction
- Standard boilerplate (severability, entire agreement, amendments)

### Step 3: Deliver

```
## Non-Disclosure Agreement

[Full NDA text with marked sections]

### Clauses Requiring Legal Review
| Clause | Why It Needs Review | Consideration |
|--------|-------------------|--------------|

### Plain-Language Summary
[What this NDA means in simple terms for non-lawyers]
```

Save as markdown. Offer to export as DOCX for signing.

## Notes

- This is a starting point — always recommend review by qualified legal counsel
- Mark any clause that involves significant legal risk with a ⚠️ flag
- Include plain-language annotations so non-lawyers understand what they're agreeing to
- Mutual NDAs are generally preferred — they're fairer and faster to negotiate
