---
name: pm-workflow-meeting-notes
description: "Summarize a meeting transcript into structured notes with decisions, action items, and follow-ups. End-to-end PM workflow for Cursor (chains multiple pm skills). Use when the user asks for /meeting-notes or a full meeting-notes workflow."
disable-model-invocation: true
---

# PM Workflow: meeting-notes

> Cursor adaptation of Claude Code `/meeting-notes`. Invoke explicitly:
> «Следуй skill pm-workflow-meeting-notes» или `@.cursor/skills/pm-workflow-meeting-notes/SKILL.md`

## Cursor notes

- Slash commands (`/meeting-notes`) недоступны — используй этот workflow skill.
- Шаги со ссылкой на **skill-name** → прочитай `.cursor/skills/<skill-name>/SKILL.md` и следуй ему.
- Сохраняй артефакты в `docs/pm/` или корень workspace, если пользователь не указал путь.
- После завершения предложи следующий workflow из секции «Next steps» исходной команды.

---


# /meeting-notes -- Meeting Summary

Transform a raw meeting transcript or rough notes into clear, structured meeting minutes with decisions captured and action items assigned.

## Invocation

```
/meeting-notes [paste transcript]
/meeting-notes [upload transcript file, audio summary, or notes]
```

## Workflow

### Step 1: Accept the Transcript

Accept in any format:
- Full transcript (from Otter, Fireflies, Google Meet, Zoom, etc.)
- Rough notes taken during the meeting
- Audio summary or meeting recap from a transcription tool
- Multiple inputs (e.g., transcript + the user's own notes)

If the input is sparse, work with what's available and flag gaps.

### Step 2: Extract and Structure

Read and follow `.cursor/skills/summarize-meeting/SKILL.md`:

Parse the content to identify:
- **Participants**: Who was present (from introductions, speaker labels, or mentions)
- **Topics discussed**: Major agenda items or conversation threads
- **Decisions made**: Explicit agreements or conclusions reached
- **Action items**: Tasks assigned, with owner and deadline if mentioned
- **Open questions**: Unresolved items that need follow-up
- **Key quotes**: Important statements worth preserving verbatim
- **Context**: Meeting type, project, and background

### Step 3: Generate Meeting Summary

```
## Meeting Summary

**Date**: [date if known]
**Participants**: [names/roles]
**Meeting type**: [standup, planning, review, 1:1, stakeholder, etc.]
**Topic**: [primary subject]

### Summary
[3-5 sentence overview of what was discussed and concluded]

### Key Decisions
1. **[Decision]** — [context and rationale]
2. ...

### Action Items
| # | Action | Owner | Deadline | Status |
|---|--------|-------|----------|--------|

### Discussion Highlights
**[Topic 1]**: [key points, different perspectives, conclusion]
**[Topic 2]**: [key points, different perspectives, conclusion]

### Open Questions
- [Question] — needs input from [person/team]

### Next Steps
- [What happens next]
- Next meeting: [if mentioned]
```

Save as markdown.

### Step 4: Offer Follow-ups

- "Want me to **email these notes** to participants?"
- "Should I **create tickets** from the action items?"
- "Want me to **draft a stakeholder update** based on the decisions made?"

## Notes

- Decisions are the most valuable output — make sure every decision is captured clearly
- Action items without owners are useless — if no owner was mentioned, flag it
- Keep the summary concise — people who weren't in the meeting should get the gist in 30 seconds
- If the transcript is very long (60+ min meeting), offer a TL;DR before the full summary
- Distinguish between "discussed" and "decided" — many topics are explored without reaching a conclusion
