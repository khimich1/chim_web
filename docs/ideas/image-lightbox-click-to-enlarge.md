# Image lightbox (click-to-enlarge)

**Проект:** `chim_web`  
**Дата:** 2026-07-25  
**Статус:** IMPLEMENT — done → [`docs/specs/image-lightbox-click-to-enlarge.md`](../specs/image-lightbox-click-to-enlarge.md) → план [`tasks/image-lightbox-click-to-enlarge.md`](../../tasks/image-lightbox-click-to-enlarge.md)

**Связано:**

- [`SPEC.md`](../../SPEC.md) §1.9.9 — `ImageViewer` (zoom / pan / rotate) на фото ответа ученика при проверке ДЗ
- [`teacher-cabinet-ux.md`](../specs/teacher-cabinet-ux.md) **US-TC-8** — lightbox + zoom в конструкторе и при проверке ДЗ
- [`clipboard-image-intake.md`](clipboard-image-intake.md) / [`clipboard-image-intake` spec](../specs/clipboard-image-intake.md) — ранее **исключали** lightbox; эта идея **supersedes** то исключение
- [`teacher-feedback-composer-ux.md`](teacher-feedback-composer-ux.md) — composer MVP явно «не трогаем lightbox»; эта идея закрывает gap
- [`student-multi-photo-answer-paste.md`](student-multi-photo-answer-paste.md) — multi-page answer gallery без dedicated lightbox
- Код: `ImageViewer`, `AuthenticatedImage`, `CustomQuestionContent`, `WrittenAnswerReview`, `ContentBlocksEditor`, `StepView`, `HomeworkFeedbackPanel`

---

## Problem Statement

How might we дать преподавателю и ученику **крупно** рассмотреть любое изображение задания / ответа / эталона / разбора (в т.ч. перевёрнутое фото рукописи), не уходя со страницы и без дублирующих UI на каждом экране?

**Для кого:** преподаватель (конструктор, review) и ученик (условие, свой ответ, эталон compare, фото разбора).  
**Когда больно:** превью «как в тестах» читаемо, но для рукописи / мелкого скрина / нескольких страниц нужно полноэкранно увеличить и повернуть; сейчас полноценный zoom/pan/rotate есть только inline в `ImageViewer` на ответе ученика в `WrittenAnswerReview`, а thumbs разбора / условие / эталон / конструктор / StepView — без lightbox.  
**Успех:** клик по любому такому изображению открывает один shared modal с zoom + rotate; закрытие возвращает на ту же страницу.

---

## Recommended Direction

**Shared `ImageLightbox` (modal overlay) + поэтапный rollout на все поверхности с task/answer/feedback images.**

1. **Один компонент** с первого дня (`ImageLightbox`): portal/modal поверх страницы; `AuthenticatedImage` внутри; жесты zoom / pan / rotate по паттернам существующего `ImageViewer` (колёсико, кнопки ↻ / сброс, pointer pan) — **без** новых npm lightbox-библиотек.
2. **Scope = everywhere**, не только review: конструктор, student StepView, teacher review, feedback thumbs, condition/reference blocks.
3. **Все изображения кликабельны** в затронутых экранах: условие, ответ ученика, эталон, превью разбора (и draft thumbs в формах, где уместно).
4. **Inline `ImageViewer` сохраняем** (Variant A) для быстрого zoom «в раскладке» на ответе ученика; плюс маленький expand-icon и click-without-drag на фото → тот же `ImageLightbox`.
5. **Галерея в модалке:** prev/next стрелки, если sibling-изображений ≥2 — включая **все image-блоки** внутри одного condition/reference блока, не только answer/feedback URL-списки.

### Locked decisions (человеком)

| # | Решение | Locked |
|---|---------|--------|
| 1 | Everywhere (teacher + student surfaces с task/answer/feedback images) — не review-only | ✅ |
| 2 | Modal: zoom **и** rotate (перевёрнутые фото) | ✅ |
| 3 | Все изображения кликабельны (condition, student answer, reference, feedback thumbs) | ✅ |
| 4 | Modal overlay на странице — не новая вкладка браузера | ✅ |
| 5 | Shared lightbox с самого начала (один компонент, rollout по экранам) | ✅ |
| 6 | **Variant A:** keep inline `ImageViewer` + open same `ImageLightbox` fullscreen | ✅ 2026-07-25 |
| 7 | **Prev/next** в модалке при ≥2 siblings — **включая** image-блоки condition/reference | ✅ 2026-07-25 |
| 8 | **Open by click on photo**; affordance = **small expand icon** (не крупная text-кнопка «fullscreen»). Static previews: click anywhere. `ImageViewer`: icon + click-without-drag (pan/drag не ломаем) | ✅ 2026-07-25 |

---

## Key Assumptions to Validate

- [x] Учителю/ученику достаточно одного shared modal; не нужен отдельный «полноэкранный режим» страницы
- [x] Variant A: inline `ImageViewer` + lightbox понятнее, чем убрать inline viewer
- [x] Prev/next в модалке для multi-page ответов, feedback gallery **и** нескольких image-блоков условия/эталона
- [x] Keyboard (Esc закрыть, ←/→ галерея) и focus trap — обязательны для a11y; touch pinch — nice-to-have, не блокер MVP если есть кнопки zoom
- [x] Blob URL из `AuthenticatedImage` / тот же auth fetch — достаточно; lightbox не требует public CDN URLs
- [x] Click-to-open не ломает pan: static = click opens; ImageViewer = expand icon + click without drag

---

## MVP Scope

**In**

- Компонент `ImageLightbox` (modal, zoom, rotate, pan, reset, close; gallery prev/next)
- Срез 1: `WrittenAnswerReview` — условие / эталон / ответ / feedback thumbs (+ связка с `ImageViewer`)
- Срез 2: `ContentBlocksEditor` — клик по превью image-блока
- Срез 3: `StepView` — иллюстрации задания + превью ответа ученика (+ эталон/compare surfaces, если там есть images)
- Срез 4: leftover thumbs — `HomeworkFeedbackPanel`, `HomeworkSubmissionPhotos`, draft previews в `StepFeedbackForm`, прочие `AuthenticatedImage` на homework/test surfaces
- Vitest: open/close, rotate/zoom controls, gallery navigation, a11y basics (Esc, role=dialog)
- Документация: эта идея + full spec + plan; cross-link из clipboard / feedback-composer / teacher-cabinet US-TC-8

**Out**

- Новые npm-пакеты lightbox / react-image-gallery и т.п.
- Annotate / рисование на фото
- Постоянное сохранение rotation на сервере
- Открытие изображения в новой вкладке / download-as-primary UX
- PDF / multi-page stitch
- Backend / API изменения

---

## Not Doing (and Why)

| Не делаем | Почему |
|-----------|--------|
| Новый npm lightbox | Жесты уже в `ImageViewer`; меньше deps и единый visual language |
| Только review-only | Locked: везде, где task/answer/feedback images |
| Новая вкладка / `window.open` | Locked: modal overlay; auth cookies + blob URL неудобны во вкладке |
| Убрать inline `ImageViewer` в MVP | Variant A locked: учитель уже пользуется in-layout zoom; lightbox — дополнение |
| Persist rotate на upload | UX для просмотра; файл на диске не меняем |
| Annotate / crop / OCR | Другие roadmap-темы (§1.9.9 out of scope) |

---

## Open Questions (resolved 2026-07-25)

| Вопрос | Решение (locked) | Было default / альтернатива |
|--------|------------------|-----------------------------|
| Inline `ImageViewer` vs только lightbox | **Variant A:** оставить inline + открытие `ImageLightbox` | Preview-only → lightbox only — отклонено |
| Multi-photo в модалке | **Prev/next** при ≥2 siblings, **включая** image-блоки condition/reference одного родителя | Только answer/feedback URL-lists — отклонено |
| Click on photo → lightbox? | **Да.** Static previews: click anywhere. `ImageViewer`: small expand icon + click-without-drag (drag = pan) | «Только кнопка, клик по image не открывает» — **OVERRIDE** |
| Affordance fullscreen | **Small icon** on/near image (не крупная text-кнопка «На весь экран») | Large text button — отклонено |
| Pinch-zoom на touch | Кнопки ± / wheel обязательны; pinch — best-effort, не блокер | Обязательный pinch — не в MVP |
| Draft thumbs в `StepFeedbackForm` до Save | Кликабельны в lightbox | Только после publish — отклонено |

Блокирующих open questions нет. Детали — ASSUMPTIONS в спеке; план — [`tasks/image-lightbox-click-to-enlarge.md`](../../tasks/image-lightbox-click-to-enlarge.md).

---

## Context (codebase)

| Артефакт | Роль |
|-----------|------|
| `frontend/components/homework/ImageViewer.tsx` | Inline zoom/pan/rotate 90° / reset; эталон жестов |
| `frontend/components/common/AuthenticatedImage.tsx` | Cookie → blob URL для `<img>` |
| `frontend/components/tests/CustomQuestionContent.tsx` | Условие / эталон blocks (сейчас без click) |
| `frontend/components/homework/WrittenAnswerReview.tsx` | Review: ImageViewer + CustomQuestionContent + feedback thumbs |
| `frontend/components/teacher/ContentBlocksEditor.tsx` | Constructor previews |
| `frontend/components/tests/StepView.tsx` | Student answer gallery thumbs |
| `SPEC.md` §1.9.9 / AC-7.12 | ImageViewer zoom/pan/rotate для фото рукописи |
| US-TC-8 (`teacher-cabinet-ux`) | Lightbox + zoom в конструкторе и проверке |
