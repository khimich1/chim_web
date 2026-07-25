# Spec: Image lightbox (click-to-enlarge)

**Версия:** 0.2.0  
**Дата:** 2026-07-25  
**Статус:** IMPLEMENT — done (2026-07-25)  
**Источник:** [`docs/ideas/image-lightbox-click-to-enlarge.md`](../ideas/image-lightbox-click-to-enlarge.md)  
**План:** [`tasks/image-lightbox-click-to-enlarge.md`](../../tasks/image-lightbox-click-to-enlarge.md)  
**Родитель:** [`SPEC.md`](../../SPEC.md) §1.9.9 (teacher review: `ImageViewer` zoom/pan/rotate); [`teacher-cabinet-ux.md`](teacher-cabinet-ux.md) **US-TC-8** (lightbox + zoom в конструкторе и при проверке ДЗ)  
**Связано:**  
- [`clipboard-image-intake.md`](clipboard-image-intake.md) — ранее **исключал** lightbox; **этот spec supersedes** то исключение (paste/DnD остаются как есть)  
- [`teacher-feedback-composer-ux.md`](teacher-feedback-composer-ux.md) — composer MVP пометил lightbox как «не трогаем»; **этот spec закрывает** US-TC-8 / click-to-enlarge  
- [`student-multi-photo-answer-paste.md`](student-multi-photo-answer-paste.md) — multi-page answers; lightbox добавляет fullscreen gallery поверх pager/list  
- Код-эталоны: `ImageViewer`, `AuthenticatedImage`, `CustomQuestionContent`

**Locked UX (2026-07-25):** Variant A (keep ImageViewer + lightbox); prev/next across condition/reference image blocks; click-on-photo opens lightbox (static = anywhere; ImageViewer = expand icon + click-without-drag).

---

## Assumptions (приняты 2026-07-25)

Если не поправите — идём в IMPLEMENT с ними:

1. **Scope = everywhere.** Lightbox на teacher **и** student surfaces, где показываются изображения задания / ответа / эталона / разбора — не только `WrittenAnswerReview`.
2. **Один shared component** `ImageLightbox` с первого среза; экраны подключаются срезами, без копипасты modal UI.
3. **Modal overlay** на текущей странице (portal / dialog). Не новая вкладка, не `window.open`, не download-as-primary.
4. **Zoom + rotate обязательны** в модалке (кнопки zoom in/out и/или wheel; rotate на **90°** как в `ImageViewer`; pan при scale > 1; кнопка «Сброс»). Upside-down рукописи — целевой кейс.
5. **Все изображения кликабельны** в затронутых экранах: условие (`question_blocks` / `CustomQuestionContent`), ответ ученика, эталон (`reference_answer`), feedback thumbs (published + draft previews в формах).
6. **Inline `ImageViewer` на ответе ученика: KEEP (Variant A).** Сохраняем in-layout zoom/pan/rotate **и** открываем тот же `ImageLightbox` через:
   - **маленький expand-icon** на/рядом с viewer (не крупная text-кнопка «На весь экран»);
   - **клик по фото без drag** → lightbox (OVERRIDE прежнего «клик не открывает»).  
   **Pan не ломаем:** pointer down → move → up с заметным перемещением = pan; click (pointer up без значимого move) = open lightbox. Expand-icon всегда открывает lightbox. Если click-without-drag окажется конфликтующим в тестах/ручной проверке — fallback: **только icon** открывает lightbox (inline pan/zoom без изменений); зафиксировать в PR notes.
7. **Галерея prev/next:** стрелки / ←→ когда `items.length ≥ 2`. Sibling-наборы включают:
   - страницы `answer_image_urls[]`;
   - `teacher_image_urls[]` / draft ids в форме;
   - **все image-блоки одного родителя** condition / reference (`CustomQuestionContent` / blocks editor context) — **не** только answer/feedback galleries.  
   Один image-блок / один URL → без стрелок.
8. **Нет новых npm lightbox libs.** Реюз `AuthenticatedImage` + жесты/паттерны из `ImageViewer` (`MIN_SCALE`/`MAX_SCALE`, wheel, pointer pan, rotate % 360). Допустимо вынести shared hook/utils (`useImageTransform`) — не обязательно в срезе 1.
9. **Auth:** только через существующий blob-fetch (`fetchAuthenticatedImageBlob` / `AuthenticatedImage`). Lightbox не меняет backend upload/RBAC.
10. **a11y MVP:** `role="dialog"` (или эквивалент), `aria-modal="true"`, Esc закрывает, focus trap на открытии, возврат фокуса на trigger; кнопки с русскими accessible names; при галерее — aria-live или видимый «N из M»; expand-icon — `aria-label` («Открыть на весь экран» / аналог).
11. **Touch pinch:** не блокер MVP. Кнопки ± и wheel на desktop обязательны; pinch — best-effort, если не усложняет.
12. **Rotate не персистится** на сервер / файл. Только UI-сессия модалки (и независимо — состояние inline `ImageViewer`).
13. **Срезы поставки:**  
    (1) `ImageLightbox` + wire `WrittenAnswerReview` (condition / reference / answer / feedback + ImageViewer expand/click)  
    (2) `ContentBlocksEditor` previews  
    (3) `StepView` student (иллюстрации задания + answer thumbs; compare/reference images если есть на том же экране)  
    (4) leftover thumbs: `HomeworkFeedbackPanel`, `HomeworkSubmissionPhotos`, draft gallery в `StepFeedbackForm`, прочие homework/test `AuthenticatedImage` без lightbox  
14. **Этот spec supersedes** явные «lightbox вне scope» в:
    - [`clipboard-image-intake.md`](clipboard-image-intake.md) idea/spec (Assumption 5 / Out of scope / Ask first)  
    - [`teacher-feedback-composer-ux.md`](teacher-feedback-composer-ux.md) Assumption 14 («не трогаем … lightbox»)  
    После approve — в тех docs добавить одну строку «lightbox → `image-lightbox-click-to-enlarge.md`» (можно в docs-задаче плана).
15. **Backend / Alembic / API** — без изменений.
16. **Не трогаем:** annotate на фото, crop, download button as primary, PDF, stitch multi-page в один JPEG, layout split `WrittenAnswerReview`, composer sheet redesign.
17. **Open triggers по типу поверхности:**
    | Поверхность | Как открыть |
    |-------------|-------------|
    | Static preview (condition / reference / feedback thumbs / constructor preview / StepView thumbs) | **Click anywhere** на изображение (+ optional small expand icon for affordance) |
    | Inline `ImageViewer` | Small expand icon **и** click-without-drag на image stage |

→ Поправьте нумерованные пункты, иначе после approve plan идём в IMPLEMENT с ними.

---

## 1. Objective

### Что строим

Единый **ImageLightbox**: клик (или expand-icon) по изображению задания / ответа / эталона / разбора открывает fullscreen modal на той же странице с **zoom, pan и rotate**, с **prev/next** по sibling-галерее при ≥2 изображениях (включая image-блоки условия/эталона).

### Зачем

Превью «как в тестах» достаточно для иллюстраций, но рукописи, скрины и перевёрнутые фото с телефона нужно рассмотреть крупно. Сейчас полноценный viewer есть только inline на ответе ученика в review (`ImageViewer`, SPEC §1.9.9 / AC-7.12); thumbs разбора, условие, эталон, конструктор и student StepView — без enlarge. US-TC-8 кабинета преподавателя прямо требует lightbox.

### Для кого

| Роль | Эффект |
|------|--------|
| **Преподаватель** | Крупно смотрит условие / эталон / ответ / фото разбора в review и превью в конструкторе |
| **Ученик** | Крупно смотрит иллюстрации задания, свои фото ответа, эталон/разбор после сдачи |

### User stories + acceptance

| ID | Story | Acceptance |
|----|--------|------------|
| US-IL-1 | Как преподаватель, кликаю превью условия/эталона в review | Открывается modal overlay; вижу крупное изображение; Esc / кнопка закрытия возвращает на review |
| US-IL-2 | Как преподаватель, увеличиваю и поворачиваю фото в lightbox | Zoom (кнопки и/или wheel) и rotate 90° работают; «Сброс» возвращает scale=1, rotation=0, offset=0 |
| US-IL-3 | Как преподаватель, листаю страницы ответа ученика в lightbox | При ≥2 `answer_image_urls` — prev/next; индекс виден; не ухожу со страницы |
| US-IL-4 | Как преподаватель, открываю lightbox из inline `ImageViewer` | Expand-icon и/или click-without-drag открывают lightbox с тем же src (siblings = все страницы шага); pan drag не открывает |
| US-IL-5 | Как преподаватель, кликаю thumb фото разбора | Lightbox открывается; при нескольких thumbs — gallery |
| US-IL-6 | Как преподаватель, кликаю image-блок в конструкторе | Lightbox на превью `ContentBlocksEditor`; несколько image-блоков в одном редакторе → gallery siblings (того же blocks list) |
| US-IL-7 | Как ученик, кликаю иллюстрацию / своё фото в StepView | Lightbox; multi-photo answer → gallery; несколько image-блоков условия → gallery |
| US-IL-8 | Как пользователь с клавиатуры, закрываю и листаю | Esc закрывает; ←/→ листают галерею когда она есть; фокус не «теряется» под оверлеем |
| US-IL-9 | Как система, auth images не ломаются | Изображения в lightbox через `AuthenticatedImage` / тот же blob path; нет broken cross-origin `<img>` |

---

## 2. Tech Stack

| Слой | Стек |
|------|------|
| Frontend | Next.js App Router, React client components (`'use client'`) |
| Images | `AuthenticatedImage` + `fetchAuthenticatedImageBlob` (`credentials: 'include'`) |
| Gestures | Паттерны из `ImageViewer` (wheel zoom, pointer pan, rotate 90°, reset) |
| Modal | Native dialog pattern или existing portal/overlay conventions в репо (без новых libs) |
| Tests | Vitest + Testing Library |
| Backend | **Без изменений** |

Новых npm/pip зависимостей **не требуется** (явно: не ставить `yet-another-react-lightbox`, `react-image-gallery`, etc.).

---

## 3. Commands

```bash
# Frontend
cd frontend
npm run dev
npm run test -- --run components/common/ImageLightbox
npm run test -- --run components/homework/WrittenAnswerReview
npm run test -- --run components/homework/ImageViewer
npm run test -- --run components/teacher/ContentBlocksEditor
npm run test -- --run components/tests/StepView
npm run lint
npm run build

# Backend — регрессия не обязательна (нет API diff); smoke по желанию:
cd backend
source .venv/bin/activate
pytest -q --co -q | head  # или полный pytest только если затронули что-то случайно
```

---

## 4. Project Structure (затрагиваемое)

```
frontend/
  components/
    common/
      AuthenticatedImage.tsx          # reuse as-is (возможно onClick wrapper снаружи)
      ImageLightbox.tsx               # NEW: modal + transform controls + optional gallery
      ImageLightbox.test.tsx          # NEW
    homework/
      ImageViewer.tsx                 # + expand icon + click-without-drag → lightbox callback
      ImageViewer.test.tsx
      WrittenAnswerReview.tsx         # wire clickables + lightbox state (slice 1)
      WrittenAnswerReview.test.tsx
      HomeworkFeedbackPanel.tsx       # slice 4
      HomeworkSubmissionPhotos.tsx    # slice 4
      StepFeedbackForm.tsx            # slice 4: draft thumbs clickable
    teacher/
      ContentBlocksEditor.tsx         # slice 2
      ContentBlocksEditor.test.tsx
    tests/
      CustomQuestionContent.tsx       # onImageClick / collect sibling image URLs
      StepView.tsx                    # slice 3
      StepView.test.tsx
docs/
  ideas/image-lightbox-click-to-enlarge.md
  specs/image-lightbox-click-to-enlarge.md   # этот файл
tasks/
  image-lightbox-click-to-enlarge.md         # plan
```

Backend — **не трогать**.

Предпочтительное размещение lightbox: `components/common/ImageLightbox.tsx` (shared teacher+student), не только `homework/`.

---

## 5. Code Style

Паттерн: controlled lightbox (open + sources + index) + тонкая обвязка на экранах; жесты рядом с `ImageViewer`.

```tsx
// frontend/components/common/ImageLightbox.tsx (иллюстрация стиля — не финальный API)
"use client";

type LightboxItem = { src: string; alt: string };

export function ImageLightbox({
  items,
  index,
  open,
  onClose,
  onIndexChange,
}: {
  items: LightboxItem[];
  index: number;
  open: boolean;
  onClose: () => void;
  onIndexChange?: (next: number) => void;
}) {
  if (!open || items.length === 0) return null;
  const current = items[index] ?? items[0];
  const showNav = items.length > 1;
  // dialog overlay + AuthenticatedImage + zoom/rotate/pan controls
  // Esc → onClose; ←/→ → onIndexChange when showNav
  return null;
}
```

- TypeScript strict; без `any`.
- Кликабельное превью: `<button type="button">` обёртка или `role="button"` + keyboard — не «голый» `<img onClick>` без a11y.
- Expand-icon: маленькая кнопка с `aria-label`, визуально secondary (не text «На весь экран»).
- Не дублировать `MIN_SCALE` / `MAX_SCALE` в трёх файлах без нужды — константы рядом с transform helper или shared с `ImageViewer`.
- Русские UI-строки кнопок («Закрыть», «Увеличить», «Уменьшить», «↻ 90°», «Сброс», «Предыдущее», «Следующее»).

---

## 6. Testing Strategy

| Уровень | Где | Что |
|---------|-----|-----|
| Component | `ImageLightbox.test.tsx` | open/close; Esc; rotate меняет transform/состояние; zoom buttons; gallery next/prev + boundary; без nav при 1 item |
| Component | `ImageViewer.test.tsx` | expand icon + click-without-drag вызывают open callback; drag-pan не вызывает open |
| Component | `WrittenAnswerReview.test.tsx` | клик по feedback thumb / condition image → lightbox; multi condition images → gallery |
| Component | ContentBlocksEditor / StepView (по срезу) | клик превью → lightbox |
| Manual | Chrome | Review multi-page answer: fullscreen + rotate upside-down; pan then click; constructor multi-image; student StepView; Esc + focus return |
| Backend | — | Не требуется |

Coverage: `ImageLightbox` happy path + gallery + Esc обязательны до merge среза 1.

---

## 7. Boundaries

### Always

- Переиспользовать `AuthenticatedImage` / cookie blob fetch.
- Modal overlay; zoom **и** rotate в lightbox.
- Vitest на lightbox до merge среза 1.
- Сохранять inline `ImageViewer` поведение (Assumption 6 / Variant A).
- Collect sibling URLs при открытии из multi-image context.
- Обновлять cross-links в clipboard / feedback-composer / US-TC-8 при docs-pass.

### Ask first

- Убрать inline `ImageViewer` gestures (переход на preview → lightbox only).
- Добавлять npm lightbox library.
- Persist rotation / crop на backend.
- Pinch-zoom как жёсткий AC MVP.
- Менять layout split `WrittenAnswerReview`.
- Откат click-without-drag на ImageViewer к icon-only (если conflict — ok как fallback, но сообщить).

### Never

- Новая browser tab как primary enlarge UX.
- Public unsigned image URLs в обход auth.
- Annotate / OCR / AI на фото в этой фиче.
- Менять upload API / MIME limits / feedback handoff.
- Коммитить секреты; трогать vendor.

---

## 8. Behaviour details

### 8.1 ImageLightbox

- Props (концепт): `open`, `items[{src,alt}]`, `index`, `onClose`, `onIndexChange?`.
- Overlay затемняет страницу; клик по backdrop **закрывает** (если не конфликтует с pan — backdrop vs image area: закрытие по backdrop / кнопке / Esc; pan только на image stage).
- Transform state **сбрасывается** при смене `index` и при `onClose` (следующее открытие — clean).
- Не зависеть от того, открыл teacher или student — один UI.
- Prev/next UI только при `items.length > 1`.

### 8.2 Wiring clickables

| Surface | Trigger | `items` |
|---------|---------|---------|
| `CustomQuestionContent` image blocks | click image (+ optional expand icon) | **все** image-блоки того же `blocks` array (gallery); index = clicked |
| `ImageViewer` | expand icon + click-without-drag | все `answer_image_urls` шага, index = текущая страница |
| Feedback thumbs | click thumb | все `teacher_image_urls` / draft urls формы |
| `ContentBlocksEditor` | click preview | **все** image-блоки текущего `blocks` list (gallery); index = clicked |
| `StepView` answer gallery | click thumb | все `answerImageUrls` шага |
| `StepView` condition images | click via CustomQuestionContent | все image-блоки условия шага |

### 8.3 ImageViewer coexistence (Variant A)

- Inline region остаётся для быстрого zoom без модалки (↻ / Сброс / wheel / pan).
- **Small expand icon** на/near image (toolbar или overlay corner) — явный affordance.
- **Click без drag** на image stage → `onExpand` / open lightbox.
- **Drag** (pointer move beyond small threshold, e.g. ~5px) → pan; **не** открывать lightbox на pointer-up.
- Не заменять существующие ↻ / Сброс text-кнопки на fullscreen text CTA.

### 8.4 Supersedes prior exclusions

Документы, где lightbox был «позже / вне scope»:

- `docs/ideas/clipboard-image-intake.md` — «Lightbox … только если всё ещё мелко»
- `docs/specs/clipboard-image-intake.md` — Assumption 5, Ask first, Out of scope
- `docs/specs/teacher-feedback-composer-ux.md` — Assumption 14
- `docs/specs/teacher-cabinet-ux.md` §8.5 — US-TC-8 «отдельная задача» → **эта** задача/spec

После approve: короткая пометка «реализуется в `image-lightbox-click-to-enlarge`», без переписывания истории paste/composer.

---

## 9. Success Criteria

- [x] Shared `ImageLightbox` существует; нет второго copy-paste modal на экранах
- [x] Срез 1: в `WrittenAnswerReview` кликабельны condition, reference, answer (expand/click), feedback thumbs; zoom + rotate в modal; multi condition images → prev/next
- [x] Multi-page answer / multi feedback thumbs / multi block images: prev/next в modal
- [x] Inline `ImageViewer` по-прежнему даёт in-layout zoom; expand icon + click-without-drag открывают lightbox; drag pans
- [x] Срезы 2–4: constructor, StepView, leftover thumbs подключены
- [x] Esc закрывает; focus trap / return; русские labels; small expand affordance
- [x] Vitest lightbox + ключевые wire-тесты зелёные; `npm run build` ок
- [x] **0** новых npm-зависимостей для lightbox
- [x] Backend diff пустой

---

## 10. Out of scope

- npm lightbox libraries
- Annotate / draw on student photo
- Server-side rotate / replace file
- PDF viewer, stitch pages
- CapturePage camera UI changes
- Composer / WrittenAnswerReview layout redesign
- Playwright E2E обязательно (желателен smoke позже)
- Push/email, OCR, AI

---

## 11. Open Questions

Блокирующие UX-вопросы **закрыты** 2026-07-25. Остаётся только ops:

| # | Тема | Default | Нужен input? |
|---|------|---------|--------------|
| Q1 | Inline ImageViewer | Variant A keep + lightbox | ✅ Locked |
| Q2 | Gallery siblings | Prev/next для URL lists **и** image-блоков condition/reference | ✅ Locked |
| Q3 | Click on photo | Static: yes; ImageViewer: icon + click-without-drag | ✅ Locked |
| Q4 | Affordance | Small expand icon (не large text) | ✅ Locked |
| Q5 | Backdrop click closes | Да | Нет, пока не возразите |
| Q6 | Pinch MVP | Не обязателен | Нет |
| Q7 | Click-without-drag threshold / fallback icon-only | ~5px move = drag; fallback icon-only if conflict | Сообщить в PR если fallback |

---

## 12. Implementation order

См. план [`tasks/image-lightbox-click-to-enlarge.md`](../../tasks/image-lightbox-click-to-enlarge.md). Не кодить до approve plan.

Порядок срезов:

1. `ImageLightbox` + unit tests (open/close/zoom/rotate/gallery/Esc)  
2. Wire `WrittenAnswerReview` + `ImageViewer` expand/click-without-drag + `CustomQuestionContent` sibling gallery  
3. `ContentBlocksEditor`  
4. `StepView`  
5. Leftover: `HomeworkFeedbackPanel`, `HomeworkSubmissionPhotos`, `StepFeedbackForm` drafts  
6. Docs cross-links (clipboard, feedback-composer, teacher-cabinet US-TC-8)
