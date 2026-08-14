---
name: pm-workflow-privacy-policy
description: "Draft a privacy policy covering data collection, usage, storage, and compliance requirements. End-to-end PM workflow for Cursor (chains multiple pm skills). Use when the user asks for /privacy-policy or a full privacy-policy workflow."
disable-model-invocation: true
---

# PM Workflow: privacy-policy

> Cursor adaptation of Claude Code `/privacy-policy`. Invoke explicitly:
> «Следуй skill pm-workflow-privacy-policy» или `@.cursor/skills/pm-workflow-privacy-policy/SKILL.md`

## Cursor notes

- Slash commands (`/privacy-policy`) недоступны — используй этот workflow skill.
- Шаги со ссылкой на **skill-name** → прочитай `.cursor/skills/<skill-name>/SKILL.md` и следуй ему.
- Сохраняй артефакты в `docs/pm/` или корень workspace, если пользователь не указал путь.
- После завершения предложи следующий workflow из секции «Next steps» исходной команды.

---


# /privacy-policy -- Privacy Policy Generator

Draft a comprehensive privacy policy for your product. Covers data types, jurisdiction, compliance (GDPR, CCPA), and marks clauses needing legal review.

## Invocation

```
/privacy-policy SaaS analytics tool that collects user behavior data — serving US and EU customers
/privacy-policy Mobile app with location data and third-party integrations
```

## Workflow

### Step 1: Gather Context

Ask:
- What product or service?
- What data is collected? (personal info, usage data, cookies, location, payment)
- Where are your users? (determines applicable regulations: GDPR, CCPA, etc.)
- Any third-party data sharing? (analytics, advertising, integrations)
- Data storage: where and how long?
- Age restrictions? (COPPA considerations)

### Step 2: Draft the Policy

Read and follow `.cursor/skills/privacy-policy/SKILL.md`:

Generate sections covering:
- What data is collected and how
- How data is used (purposes)
- Legal basis for processing (GDPR)
- Data sharing and third parties
- Data retention and deletion
- User rights (access, deletion, portability, opt-out)
- Cookie policy
- Security measures
- Children's privacy (if applicable)
- International transfers
- Contact information
- Policy update process

### Step 3: Deliver

```
## Privacy Policy: [Product]

[Full policy text]

### Compliance Checklist
| Regulation | Status | Notes |
|-----------|--------|-------|

### Clauses Requiring Legal Review
| Clause | Why | Priority |
|--------|-----|----------|

### Implementation Checklist
- [ ] Cookie consent banner
- [ ] Data subject request process
- [ ] Data processing records
- [ ] DPA with processors
```

Save as markdown. Offer DOCX export.

## Notes

- This is a template — legal counsel should review before publishing
- GDPR and CCPA have specific requirements that can't be approximated — flag where expert review is essential
- Privacy policies should be in plain language, not legalese
- Update the policy when data practices change, not just annually
