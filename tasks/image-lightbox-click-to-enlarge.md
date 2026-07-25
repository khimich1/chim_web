# Implementation Plan: Image lightbox (click-to-enlarge)

**Источник:** [`docs/specs/image-lightbox-click-to-enlarge.md`](../docs/specs/image-lightbox-click-to-enlarge.md) v0.2.0 · idea: [`docs/ideas/image-lightbox-click-to-enlarge.md`](../docs/ideas/image-lightbox-click-to-enlarge.md)  
**Дата плана:** 2026-07-25  
**Статус:** IMPLEMENT — done  
**Skills:** planning-and-task-breakdown → incremental-implementation → TDD  
**Коммиты:** только по явной просьбе пользователя  
**Approve:** 2026-07-25 — go (IL-1…IL-8; gallery siblings = all image blocks; click-without-drag fallback icon-only OK; expand icon only on ImageViewer)

### Progress

| Task | Статус |
|------|--------|
| IL-1 ImageLightbox + vitest | ✅ |
| IL-2 CustomQuestionContent sibling click API | ✅ |
| IL-3 ImageViewer expand + click-without-drag | ✅ |
| IL-4 WrittenAnswerReview wire (slice 1) | ✅ |
| IL-5 ContentBlocksEditor (slice 2) | ✅ |
| IL-6 StepView (slice 3) | ✅ |
| IL-7 Leftover thumbs (slice 4) | ✅ |
| IL-8 Docs cross-links | ✅ |

**PR / plan note:** click-without-drag (~5px) implemented and covered by vitest; icon-only fallback not needed. Static previews = click-anywhere only (no expand icon) per approve Q4.

---

## Overview

Shared `ImageLightbox` modal (zoom / pan / rotate / Esc / backdrop / prev-next) без новых npm-библиотек; жесты по паттернам `ImageViewer` + `AuthenticatedImage`. Variant A: inline viewer на ответе ученика остаётся; lightbox открывается expand-icon + click-without-drag. Static previews — click anywhere. Gallery siblings включают image-блоки condition/reference, не только answer/feedback URL-lists. Rollout по срезам спеки: foundation → WrittenAnswerReview → constructor → StepView → leftover thumbs → docs.

---

## Architecture Decisions

| Решение | Выбор | Почему |
|---------|--------|--------|
| Component location | `frontend/components/common/ImageLightbox.tsx` | Shared teacher+student; не homework-only |
| API shape | Controlled: `open`, `items[{src,alt}]`, `index`, `onClose`, `onIndexChange?` | Спека §5; родитель владеет gallery state |
| Auth images | `AuthenticatedImage` внутри lightbox | Spec Assump. 8–9; cookie blob path |
| Gestures | Copy/adapt ImageViewer wheel + pointer pan + rotate 90° + reset; optional later `useImageTransform` | Нет новых libs; единый feel |
| Gallery siblings | Collect all image URLs from current multi-image context | Locked: answer pages, feedback thumbs, **и** image-блоки одного blocks array |
| Static open | Click anywhere on preview (+ optional small expand icon) | Locked 2026-07-25 |
| ImageViewer open | Small expand icon + click-without-drag (~5px threshold); drag = pan | Locked; fallback icon-only if conflict |
| Affordance | Small icon, не large «На весь экран» text | Locked |
| CustomQuestionContent | Optional `onImageClick?(items, index)` — родитель открывает lightbox | Один click-API для condition/reference на review + StepView |
| Backend | Нет изменений | Spec Assump. 15 |
| npm | 0 новых lightbox deps | Spec Assump. 8 |

**As-is (проверено в коде):**

- `ImageViewer`: scale/rotation/offset, wheel, pointer pan, ↻ / Сброс; **нет** expand / lightbox callback.
- `CustomQuestionContent`: рендерит `AuthenticatedImage` для image-блоков; **нет** onClick / sibling collect.
- `WrittenAnswerReview`: condition + reference через `CustomQuestionContent`; answer через `ImageViewer` per page; feedback thumbs — `AuthenticatedImage` без click.
- `ContentBlocksEditor` / `StepView` / leftover panels — previews без lightbox.

**ДОПУЩЕНИЯ (из spec v0.2.0, locked 2026-07-25):**
1. Everywhere (teacher + student).
2. Один shared `ImageLightbox`.
3. Modal overlay (не новая вкладка).
4. Zoom + rotate + pan + reset в модалке.
5. Все task/answer/reference/feedback images кликабельны на затронутых экранах.
6. Variant A: keep ImageViewer + lightbox via expand icon + click-without-drag.
7. Prev/next при ≥2 siblings, включая condition/reference image-блоки.
8. Нет новых npm lightbox libs.
9. Auth через AuthenticatedImage / blob fetch.
10. a11y: dialog, Esc, focus trap, русские labels, «N из M».
11. Pinch — nice-to-have, не блокер.
12. Rotate не персистится.
13. Срезы 1→4 как phases ниже.
14. Supersedes clipboard / feedback-composer lightbox exclusions (docs в IL-8).
15. Backend без изменений.
16. Не трогаем annotate / PDF / layout redesign.
17. Static = click anywhere; ImageViewer = icon + click-without-drag.

→ Поправь сейчас, иначе после «ок / implement» идём с этим.

---

## Dependency graph

```
IL-1 ImageLightbox (+ vitest)
        │
        ├── IL-2 CustomQuestionContent onImageClick / siblings
        │         │
        └── IL-3 ImageViewer expand + click-without-drag
                  │
                  └── IL-4 WrittenAnswerReview wire (slice 1 demo)
                            │
                            └── Checkpoint A

IL-5 ContentBlocksEditor (slice 2)     ← after IL-1
        │
IL-6 StepView (slice 3)                ← after IL-1 + IL-2
        │
        └── Checkpoint B

IL-7 Leftover thumbs (slice 4)         ← after IL-1
        │
IL-8 Docs cross-links
        │
        └── Checkpoint C (complete)
```

**Параллельно после IL-1:** IL-2 и IL-3 независимы; IL-5 / IL-7 можно начать после Checkpoint A (или параллельно IL-4 если агенты разные — предпочтительно после A, чтобы API lightbox стабилен).  
**IL-6** зависит от IL-2 (condition click API).  
**Минимум для демо учителю (review):** IL-1…IL-4.

**Порядок срезов спеки:** Phase 1 = foundation + slice 1; Phase 2 = slice 2; Phase 3 = slice 3; Phase 4 = slice 4 + docs.

---

## Task List

### Phase 1: Foundation + WrittenAnswerReview (spec slice 1)

---

## Task IL-1: `ImageLightbox` + vitest

**Description:** Новый shared client component: modal/dialog overlay с `AuthenticatedImage`, zoom (± / wheel), pan на image stage, rotate 90°, сброс, закрытие (Esc, кнопка, backdrop). При `items.length > 1` — prev/next + ←/→ + видимый «N из M». Transform state сбрасывается при смене index и при close. Без npm lightbox libs.

**Acceptance criteria:**
- [ ] Props: `open`, `items`, `index`, `onClose`, `onIndexChange?`; при `!open` / empty — null
- [ ] `role="dialog"` + `aria-modal="true"`; русские accessible names кнопок
- [ ] Zoom / rotate / reset / pan работают; Esc и backdrop закрывают
- [ ] Gallery: next/prev + keyboard; нет стрелок при 1 item
- [ ] Vitest: open/close, Esc, zoom/rotate, gallery boundary, no-nav single

**Verification:**
- [ ] `cd frontend && npm run test -- --run components/common/ImageLightbox`

**Dependencies:** None

**Files likely touched:**
- `frontend/components/common/ImageLightbox.tsx` (NEW)
- `frontend/components/common/ImageLightbox.test.tsx` (NEW)

**Estimated scope:** M

---

## Task IL-2: `CustomQuestionContent` — sibling click API

**Description:** Сделать image-блоки кликабельными: собрать все image `{src,alt}` из `blocks`, по клику вызвать `onImageClick?.(items, index)`. a11y: button wrapper / keyboard. Без `onImageClick` — поведение как сейчас (или click no-op). Не рендерить lightbox внутри — только callback.

**Acceptance criteria:**
- [ ] Клик по image-блоку → `onImageClick(items, index)` где `items` = все image-блоки родителя
- [ ] Один image → `items.length === 1`
- [ ] Без `onImageClick` — нет ошибок (click optional)
- [ ] Vitest: multi-image click передаёт полный sibling list + index

**Verification:**
- [ ] `npm run test -- --run components/tests/CustomQuestionContent`

**Dependencies:** None (можно параллельно IL-1; wire в IL-4)

**Files likely touched:**
- `frontend/components/tests/CustomQuestionContent.tsx`
- `frontend/components/tests/CustomQuestionContent.test.tsx`

**Estimated scope:** S

---

## Task IL-3: `ImageViewer` — expand icon + click-without-drag

**Description:** Добавить optional `onExpand?: () => void`. Small expand-icon (aria-label «Открыть на весь экран» / аналог) всегда вызывает `onExpand`. Click-without-drag на image stage: pointer move > ~5px → pan only; pointer up без drag → `onExpand`. Существующие ↻ / Сброс / wheel / pan без регрессий. Не добавлять large text «На весь экран».

**Acceptance criteria:**
- [ ] Expand icon видим и вызывает `onExpand`
- [ ] Click без drag → `onExpand`; drag → pan, no expand
- [ ] Без `onExpand` — icon скрыт или disabled; pan/zoom как раньше
- [ ] Vitest: icon click; click-without-drag; drag does not fire expand

**Verification:**
- [ ] `npm run test -- --run components/homework/ImageViewer`

**Dependencies:** None (wire в IL-4)

**Files likely touched:**
- `frontend/components/homework/ImageViewer.tsx`
- `frontend/components/homework/ImageViewer.test.tsx`

**Estimated scope:** M

---

## Task IL-4: Wire `WrittenAnswerReview` (slice 1)

**Description:** Один lightbox state на review step: condition / reference через `CustomQuestionContent.onImageClick` (siblings = image-блоки того blocks array); answer — `ImageViewer.onExpand` с `items = answer_image_urls`, index = текущая страница; feedback thumbs — click → `teacher_image_urls` gallery. Подключить `ImageLightbox`.

**Acceptance criteria:**
- [ ] Клик condition/reference image → lightbox; ≥2 image-блока → prev/next
- [ ] Expand / click-without-drag на answer ImageViewer → lightbox с pages gallery
- [ ] Клик feedback thumb → lightbox; multi thumbs → gallery
- [ ] Esc / close возвращает на review; inline ImageViewer zoom всё ещё работает
- [ ] Vitest: минимум 2 wire-кейса (thumb + condition или expand)

**Verification:**
- [ ] `npm run test -- --run components/homework/WrittenAnswerReview`
- [ ] `npm run test -- --run components/common/ImageLightbox`
- [ ] Manual: review multi-page answer + upside-down rotate + pan then click

**Dependencies:** IL-1, IL-2, IL-3

**Files likely touched:**
- `frontend/components/homework/WrittenAnswerReview.tsx`
- `frontend/components/homework/WrittenAnswerReview.test.tsx`

**Estimated scope:** M

---

### Checkpoint A: After IL-1…IL-4

- [x] Vitest ImageLightbox + ImageViewer + CustomQuestionContent + WrittenAnswerReview зелёные
- [ ] Manual smoke: review — condition gallery, answer expand, feedback thumbs, Esc
- [ ] Pan на ImageViewer не открывает lightbox случайно
- [x] 0 новых npm deps; backend untouched
- [ ] **Human review** перед Phase 2–4 (особенно click-vs-pan feel)

---

### Phase 2: Constructor (spec slice 2)

---

## Task IL-5: `ContentBlocksEditor` — preview → lightbox

**Description:** Клик по image-preview блока открывает `ImageLightbox` с siblings = все image-блоки текущего `blocks` list, index = clicked. Не ломать paste/DnD/upload/edit. Small expand affordance optional (click anywhere достаточно).

**Acceptance criteria:**
- [ ] Клик preview → lightbox с корректным src
- [ ] ≥2 image-блока в editor → prev/next в модалке
- [ ] Paste/DnD/intake регрессий нет
- [ ] Vitest: click preview → dialog visible

**Verification:**
- [ ] `npm run test -- --run components/teacher/ContentBlocksEditor`
- [ ] Manual: `/teacher/...` конструктор — enlarge image block

**Dependencies:** IL-1 (желательно после Checkpoint A)

**Files likely touched:**
- `frontend/components/teacher/ContentBlocksEditor.tsx`
- `frontend/components/teacher/ContentBlocksEditor.test.tsx`

**Estimated scope:** M

---

### Phase 3: Student StepView (spec slice 3)

---

## Task IL-6: `StepView` — condition + answer thumbs

**Description:** Подключить lightbox: condition/reference images через `CustomQuestionContent.onImageClick`; answer gallery thumbs — click → sibling `answerImageUrls`. Compare/reference surfaces на том же экране, если есть images — тот же паттерн. Не ломать intake/paste/QR.

**Acceptance criteria:**
- [ ] Клик иллюстрации условия → lightbox; multi image-блоки → gallery
- [ ] Клик answer thumb → lightbox; multi pages → gallery
- [ ] Intake / attach / QR без регрессий
- [ ] Vitest: click thumb / condition → dialog (расширить существующие тесты)

**Verification:**
- [ ] `npm run test -- --run components/tests/StepView`
- [ ] Manual: student step с multi-photo answer + условие с картинками

**Dependencies:** IL-1, IL-2

**Files likely touched:**
- `frontend/components/tests/StepView.tsx`
- `frontend/components/tests/StepView.test.tsx`

**Estimated scope:** M

---

### Checkpoint B: After IL-5…IL-6

- [x] Constructor + StepView vitest зелёные
- [ ] Manual: teacher constructor + student StepView enlarge
- [x] Gallery siblings корректны (не смешивать answer URLs с condition blocks)

---

### Phase 4: Leftover thumbs + docs (spec slice 4)

---

## Task IL-7: Leftover — FeedbackPanel / SubmissionPhotos / StepFeedbackForm drafts

**Description:** Подключить `ImageLightbox` к оставшимся homework thumbs: `HomeworkFeedbackPanel`, `HomeworkSubmissionPhotos`, draft previews в `StepFeedbackForm`. Click anywhere; siblings = список URL на той поверхности. Не менять upload/save/QR semantics.

**Acceptance criteria:**
- [ ] Клик published feedback thumbs → lightbox (+ gallery если multi)
- [ ] Submission photos кликабельны
- [ ] Draft thumbs в `StepFeedbackForm` до Save открывают lightbox
- [ ] Vitest: хотя бы по одному кейсу на затронутый компонент с существующими тестами

**Verification:**
- [ ] `npm run test -- --run components/homework/HomeworkFeedbackPanel`
- [ ] `npm run test -- --run components/homework/HomeworkSubmissionPhotos`
- [ ] `npm run test -- --run components/homework/StepFeedbackForm`
- [ ] Manual: review leftover surfaces

**Dependencies:** IL-1

**Files likely touched:**
- `frontend/components/homework/HomeworkFeedbackPanel.tsx`
- `frontend/components/homework/HomeworkFeedbackPanel.test.tsx`
- `frontend/components/homework/HomeworkSubmissionPhotos.tsx`
- `frontend/components/homework/HomeworkSubmissionPhotos.test.tsx`
- `frontend/components/homework/StepFeedbackForm.tsx`
- `frontend/components/homework/StepFeedbackForm.test.tsx`

**Estimated scope:** M

---

## Task IL-8: Docs cross-links

**Description:** Короткие пометки «lightbox → `image-lightbox-click-to-enlarge`» в clipboard idea/spec, teacher-feedback-composer spec (Assump. 14), teacher-cabinet-ux US-TC-8. Spec status → IMPLEMENT после начала кода. Не переписывать историю paste/composer.

**Acceptance criteria:**
- [ ] Cross-links в clipboard / feedback-composer / teacher-cabinet docs
- [ ] Idea + spec указывают на этот plan path
- [ ] Нет противоречащих «lightbox out of scope» без ссылки на supersede

**Verification:**
- [ ] Grep docs на «lightbox» — противоречия сняты или помечены supersede

**Dependencies:** Can run anytime after plan approve; ideally after Checkpoint A or with final slice

**Files likely touched:**
- `docs/ideas/clipboard-image-intake.md`
- `docs/specs/clipboard-image-intake.md`
- `docs/specs/teacher-feedback-composer-ux.md`
- `docs/specs/teacher-cabinet-ux.md`
- optionally status line in `docs/specs/image-lightbox-click-to-enlarge.md`

**Estimated scope:** S

---

### Checkpoint C: Complete

- [x] Все IL-1…IL-8 acceptance зелёные (vitest)
- [x] `npm run test` (затронутые suites) ok; `npm run build` — see session
- [ ] Spec success criteria §9 — human manual smoke remaining
- [x] Backend diff пустой
- [ ] Ready for code-review-and-quality

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Click-without-drag ломает pan на ImageViewer | Med | ~5px threshold + vitest; fallback icon-only (Assump. 6); human check Checkpoint A |
| Двойной transform state (inline vs modal) путает | Low | Modal всегда reset on open/index change; inline state независим |
| Sibling collect смешивает разные контексты | Med | Явные items per open call; не глобальный «все картинки страницы» |
| Focus trap / portal a11y gaps | Med | Vitest Esc + role; manual Tab; reuse existing dialog patterns if any |
| Scope creep leftover AuthenticatedImage everywhere | Low | IL-7 только listed files; новые surfaces — Ask first |
| ContentBlocksEditor click vs delete/edit controls | Med | Click target = preview image only, не toolbar buttons |

---

## Open Questions (for human before IMPLEMENT)

Блокирующих UX нет (locked 2026-07-25). Подтвердить план:

1. **Approve plan IL-1…IL-8** as scoped?
2. **ContentBlocksEditor gallery:** siblings = all image-блоки в текущем `blocks` list редактора (не только соседние) — ok?
3. **Click-without-drag fallback:** если pan conflict — icon-only без отдельного re-approve, только PR note — ok?
4. **Optional expand icon на static previews** (кроме ImageViewer) — skip в MVP (click anywhere достаточно), icon только на ImageViewer — ok?

---

## Parallelization notes

| After | Safe parallel |
|-------|---------------|
| IL-1 done | IL-2 ‖ IL-3; later IL-5 ‖ IL-7 |
| IL-2 + IL-1 | IL-6 |
| IL-1+2+3 | IL-4 (sequential preferred) |
| Anytime | IL-8 docs |

Не параллелить два агента на одном файле (`WrittenAnswerReview`, `StepView`).
