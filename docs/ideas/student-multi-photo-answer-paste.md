# Student multi-photo answer + clipboard paste

## Problem Statement
How Might We дать ученику на self-check в ДЗ прикрепить до 3 фото/скринов ответа (в т.ч. из буфера, с фокусом в «Ваш ответ») так же естественно, как учитель вставляет картинки в конструкторе — не убирая текстовое поле?

## Recommended Direction
**Мультифото на шаг (`answer_image_ids[]`, max 3) + общая intake-зона вокруг «ответ + фото».**

Сейчас одно FK `answer_image_id`; paste висит только под полем ответа — Ctrl+V с фокусом в инпуте не цепляет картинку. Текст ответа оставляем. Paste/DnD/file/QR **добавляют** в галерею до лимита 3; для compare в ДЗ достаточно ≥1 фото. У учителя — листание страниц в review (`ImageViewer` / submission photos), не склейка в один JPEG.

Переиспользуем `imageFilesFromDataTransfer` / `IMAGE_INTAKE_HINT` из clipboard-intake; меняем контракт шага и handoff.

## Key Assumptions to Validate
- [ ] **A:** 3 страниц хватает большинству рукописных ответов — проверить на 5–10 реальных ДЗ
- [ ] **C:** image в буфере + фокус в «Ваш ответ» → attach; text-only paste в поле не ломается
- [ ] **D:** QR/handoff умеет **добавить** 2-ю/3-ю страницу, а не только заменить первое фото
- [ ] Учителю удобно листать 2–3 фото в существующем viewer без нового lightbox

## MVP Scope
**In**
- Backend: `answer_image_ids` (JSON, ≤3) + миграция; compat со старым `answer_image_id` или replace
- Attach/remove до `checked`; compare/submit: ≥1 id в ДЗ
- StepView: intake на обёртке ответа+фото; paste/DnD/file; превью галереи; лимит 3
- Handoff: добавить фото, пока `<3`
- Teacher review / submission photos: все URL шага
- Vitest + pytest на лимит, paste из поля ответа, RBAC

**Out of MVP:** склейка страниц, PDF, >3, пересъёмка после `checked`, убрать текст

## Not Doing (and Why)
- Убирать «Ваш ответ» — нужно для короткого текста/подписи
- Склейка в один JPEG — хрупко и хуже проверке
- Лимит 5 как у teacher feedback — для ученика достаточно 3
- CapturePage как конструктор — остаётся camera-first
- Безлимит / альбом — раздувает storage и review

## Open Questions (resolved for spec)
- Миграция: колонка JSON `answer_image_ids` + backfill из `answer_image_id`, затем drop FK — FE/BE в одном релизе
- Удаление одного фото из галереи до compare — **да** в MVP
- Порядок страниц: порядок добавления; **без** reorder в MVP

## Context (codebase)
- `TestSessionStep.answer_image_id` — `backend/app/models/test_session.py`
- Student UI — `frontend/components/tests/StepView.tsx`
- Teacher pattern — `frontend/components/teacher/ContentBlocksEditor.tsx`
- Shared intake — `frontend/lib/image-intake.ts`
- Prior Not Doing multi-photo — `docs/ideas/written-homework-photo-submit.md`
- Clipboard intake (1 photo) — `docs/specs/clipboard-image-intake.md` US-CI-4
