# Spec: Clipboard / DnD image intake

**Версия:** 0.1.1  
**Дата:** 2026-07-24  
**Статус:** IMPLEMENT ✅ — срезы CI-1…CI-5 выполнены; ручная проверка в Chrome желательна  
**Источник:** [`docs/ideas/clipboard-image-intake.md`](../ideas/clipboard-image-intake.md)  
**Родитель:** [`SPEC.md`](../../SPEC.md) §1.9 (конструктор / content blocks), uploads  
**Связано:** [`teacher-cabinet-ux.md`](teacher-cabinet-ux.md) US-TC-3 (paste) — **этот документ = детальная спецификация media intake**; lightbox (US-TC-8) **вне scope** здесь
**План:** [`tasks/clipboard-image-intake.md`](../../tasks/clipboard-image-intake.md)

---

## Assumptions (проверьте до PLAN)

Если не поправите — считаем принятыми:

1. **Только frontend.** Backend `/api/uploads/images` и схема блоков `text | image` не меняются.
2. **Вставка блока:** если известен индекс «активного» блока (фокус в textarea) — image-блок вставляется **сразу после него**; иначе — **в конец** списка. Для экранов без блоков (StepView / feedback / capture) — тот же upload-flow, что у file picker (append / replace по правилам экрана).
3. **Paste с `image/*`:** всегда `preventDefault()` на контейнере intake, чтобы filename/binary не попадали в textarea. Обычный text paste в textarea **не ломается** (handler не вызывает preventDefault, если в clipboard нет image).
4. **MIME:** только `image/jpeg`, `image/png`, `image/webp` — как у текущего file picker. Иное → сообщение об ошибке, без upload.
5. **Отображение «как в тестах»:** классы эталона  
   `my-3 block h-auto max-w-full rounded-md border border-zinc-200 object-contain`  
   (см. `CustomQuestionContent` / `QuestionContent`). Без lightbox / `ImageViewer` в этом релизе. В `ContentBlocksEditor` превью через `AuthenticatedImage` (убрать дублирующий `BlockImagePreview` fetch, если возможно без регрессий).
6. **StepFeedbackForm:** сейчас превью `h-20 w-20 object-cover` — слишком мелко. В рамках этой фичи превью фидбек-фото → читаемый размер (не крошечный crop; `object-contain`, ширина до контейнера или разумный `max-h` ≥ ~16rem). Лимит 5 фото без изменений.
7. **Порядок поставки (срезы):**  
   (1) shared intake + `ContentBlocksEditor` + display в редакторе + **видимый hint**  
   (2) `StepView`  
   (3) `StepFeedbackForm` (+ размер превью)  
   **CapturePage — вне MVP** (см. Assumption 11): телефонная съёмка по QR для рукописного ДЗ; paste/DnD там низкая ценность и путает camera-first UX. Later — отдельная задача, если понадобится.  
8. **Desktop-first.** Mobile: file picker / камера как сейчас; clipboard paste на iOS/Android не обязателен в MVP.
9. **Multi-file drop / multi-image paste:** загружаем **все** подходящие файлы **до лимита экрана** (по порядку в DataTransfer):
   | Экран | Лимит |
   |-------|--------|
   | `ContentBlocksEditor` | до **10** image-файлов за одно drop/paste-событие (мягкий потолок; лишние игнор + короткое сообщение) |
   | `StepFeedbackForm` | до заполнения слотов (**макс. 5** фото всего на форму) |
   | `StepView` | **superseded:** лимит **3** фото на шаг (`answer_image_ids[]`), append до заполнения — см. [`student-multi-photo-answer-paste.md`](student-multi-photo-answer-paste.md). Ранее здесь был limit=1 (replace). |
10. **UI hint обязателен** на каждой зоне intake в MVP: короткий текст вроде «Можно вставить из буфера (Ctrl+V) или перетащить файл».
11. **CapturePage** = страница `/capture?token=…` для ученика: чеклист + камера/файл → handoff фото ДЗ. **Не** конструктор заданий. В этот релиз **не** подключаем.
12. **Этот spec supersedes** краткое описание paste в `teacher-cabinet-ux.md` §8 (media). После approve — в teacher-cabinet добавить ссылку «детали → clipboard-image-intake.md»; lightbox остаётся отдельной задачей cabinet UX.

→ Поправьте нумерованные пункты, иначе после approve идём в PLAN с ними.

---

## 1. Objective

### Что строим

Единый клиентский **image intake**: Ctrl/Cmd+V (картинка в буфере), drag-and-drop и file picker → `uploadImage` → существующая модель (image-блок или image id экрана). Превью и показ заданий — **читаемый размер**, как иллюстрации в тестах.

### Зачем

Сейчас учитель сохраняет скрин в файл и выбирает через «+ Изображение». В фидбеке превью крошечные. Это замедляет сборку заданий и проверку.

### Для кого

| Роль | Эффект |
|------|--------|
| **Преподаватель** | Вставляет скрин в вопрос/эталон и в разбор ДЗ без file dialog |
| **Ученик** | Может вставить/перетащить картинку ответа в тесте (StepView); видит крупные иллюстрации в заданиях |

### User stories + acceptance

| ID | Story | Acceptance |
|----|--------|------------|
| US-CI-1 | Как преподаватель, вставляю скрин из буфера в конструкторе | Фокус в `ContentBlocksEditor` → Ctrl/Cmd+V с PNG/JPEG/WebP → upload → новый image-блок; text paste в textarea работает |
| US-CI-2 | Как преподаватель, перетаскиваю файлы на редактор | Drop 1..N image (N≤10) → N image-блоков; лишние отсекаются с сообщением |
| US-CI-2b | Как преподаватель, вижу подсказку про paste/DnD | В зоне редактора есть видимый hint про Ctrl+V и перетаскивание |
| US-CI-3 | Как преподаватель, вижу крупное превью в редакторе | Image-блок не меньше «как в тесте» (`max-w-full`, без мелкого thumbnail) |
| US-CI-4 | Как ученик, вставляю/дропаю ответ-картинку в StepView | Paste/DnD вызывают тот же путь, что file input → `attachAnswerImage` (**актуальный лимит/галерея:** [`student-multi-photo-answer-paste.md`](student-multi-photo-answer-paste.md)) |
| US-CI-5 | Как преподаватель, вставляю фото в StepFeedbackForm | Paste/DnD при `<5` фото; превью читаемое, не 80×80 crop |
| US-CI-6 | Как система, отклоняю не-image | GIF/PDF/текст-only clipboard → нет upload; ошибка или no-op для text |

---

## 2. Tech Stack

| Слой | Стек |
|------|------|
| Frontend | Next.js App Router, React client components, Clipboard / Drag-and-Drop DOM APIs |
| Upload | Существующий `uploadImage` → `POST /api/uploads/images` |
| Auth images | `AuthenticatedImage` / cookies `credentials: 'include'` |
| Tests | Vitest + Testing Library; mock `uploadImage` |
| Backend | **Без изменений** |

Новых npm/pip зависимостей **не требуется**.

---

## 3. Commands

```bash
# Frontend
cd frontend
npm run dev
npm run test
npm run test -- ContentBlocksEditor
npm run test -- image-intake
npm run lint
npm run build

# Backend (регрессия uploads, без новых тестов обязательно)
cd backend
source .venv/bin/activate
pytest tests/ -k upload -q
```

---

## 4. Project Structure (затрагиваемое)

```
frontend/
  lib/
    image-intake.ts              # NEW: extractImageFile(clipboard|drag) → File | null
                                #       isAllowedImageFile(file) → boolean
  hooks/                        # или рядом с lib — по конвенции репо
    useImageIntake.ts           # NEW (опционально): onPaste/onDrop/onDragOver handlers
  components/
    teacher/ContentBlocksEditor.tsx   # wire intake + display
    teacher/ContentBlocksEditor.test.tsx  # NEW или расширить
    tests/StepView.tsx                  # wire intake
    homework/StepFeedbackForm.tsx       # wire intake + larger preview
    common/AuthenticatedImage.tsx       # reuse for editor preview
    # CapturePage.tsx — вне MVP (не трогаем)
    tests/CustomQuestionContent.tsx     # эталон display (не менять без нужды)
docs/
  ideas/clipboard-image-intake.md
  specs/clipboard-image-intake.md        # этот файл
```

Backend routers/services — **не трогать**.

---

## 5. Code Style

Паттерн: чистые функции + тонкая обвязка в UI (как `uploadImage` отдельно от компонента).

```ts
// frontend/lib/image-intake.ts (иллюстрация стиля)
const ALLOWED = new Set(["image/jpeg", "image/png", "image/webp"]);

export function isAllowedImageMime(mime: string): boolean {
  return ALLOWED.has(mime);
}

/** Первый image/* файл из clipboard; иначе null. */
export function imageFileFromClipboard(data: DataTransfer | null): File | null {
  if (!data) return null;
  for (const item of Array.from(data.items)) {
    if (item.kind === "file" && item.type.startsWith("image/")) {
      const file = item.getAsFile();
      if (file && isAllowedImageMime(file.type)) return file;
    }
  }
  return null;
}
```

- TypeScript strict; без `any`.
- Ошибки upload → существующий `ApiError` / русское сообщение в UI.
- Не дублировать MIME-список в четырёх компонентах — одна константа/helper.

---

## 6. Testing Strategy

| Уровень | Где | Что |
|---------|-----|-----|
| Unit | `frontend/lib/image-intake.test.ts` | MIME filter; clipboard DataTransfer mock → File; non-image → null |
| Component | `ContentBlocksEditor.test.tsx` | paste image → `uploadImage` called → onChange с image-блоком; text paste не preventDefault path; drop file |
| Component | StepFeedbackForm / StepView (по срезу) | paste/DnD → upload; лимит 5 в feedback |
| Manual | Chrome desktop | PrintScreen → Ctrl+V в конструкторе; DnD PNG; text Ctrl+V в textarea |
| Backend | — | Не требуется для MVP |

Coverage: новые helpers + happy-path paste в редакторе обязательны до merge среза 1.

---

## 7. Boundaries

### Always
- Переиспользовать `uploadImage` и allowlist MIME backend.
- `preventDefault` только когда в событии есть image для intake.
- Тесты (vitest) на helper + ContentBlocksEditor перед merge среза 1.
- Сохранять text paste в textarea.

### Ask first
- Подключать paste/DnD к `CapturePage` (сейчас вне MVP).
- Менять лимиты (10 за drop / 5 в feedback).
- Lightbox / zoom (это teacher-cabinet US-TC-8).
- Новые npm-зависимости.

### Never
- Менять API блоков / backend upload contract в этой фиче.
- Inline/rich-text image внутри text-блока.
- Класть секреты в клиент; менять auth cookies.
- Подменять эталон размера на `ImageViewer` с `max-h-72` для заданий конструктора.

---

## 8. Behaviour details

### 8.1 Shared intake

Вход: `ClipboardEvent` | `DragEvent` | `File` из `<input type="file">`.  
Выход: `File` или ошибка «формат не поддерживается».

Состояния UI: uploading (disable повторный paste/drop), error alert (как сейчас в редакторе).

### 8.2 ContentBlocksEditor

- Обёртка списка блоков + кнопок: `onPaste`, `onDragOver`, `onDrop` (tabIndex / role по a11y: зона должна получать paste при фокусе внутри).
- После успешного upload: `{ type: "image", url }` в позицию по Assumption 2.
- File picker без изменений по контракту.
- **Обязательный** hint (видимый текст): «Можно вставить изображение из буфера (Ctrl+V) или перетащить файл».
- Multi-file: см. Assumption 9 (до 10 за событие).

### 8.3 Display

- Редактор и ученик (custom question): одинаковый визуальный контракт «full width of content column».
- Не вводить отдельный max-width меньше родителя.

### 8.4 StepView / StepFeedbackForm

- Тот же extract → существующий `handle*Upload(file)` (последовательно для N файлов до лимита).
- Feedback: увеличить превью (Assumption 6); paste/drop disabled при `imageIds.length >= 5`; hint обязателен.

---

## 9. Success Criteria

- [x] Ctrl/Cmd+V со скриншотом в конструкторе создаёт image-блок без порчи текста в textarea
- [x] Drag-and-drop PNG/JPEG/WebP в конструкторе работает
- [x] Превью в редакторе визуально сопоставимо с иллюстрацией в тесте (не thumbnail)
- [x] Vitest: helper + paste path ContentBlocksEditor зелёные
- [x] Срезы 2–3: paste/DnD в StepView и StepFeedbackForm; превью фидбека читаемое
- [x] Видимый hint на зонах intake
- [x] Backend diff пустой (или только docs)
- [x] CapturePage **не** изменён в этом релизе

---

## 10. Out of scope

- Rich-text / inline images in text blocks
- Lightbox, rotate, pan (`ImageViewer`)
- `CapturePage` paste/DnD (later, отдельная задача)
- Mobile clipboard paste guarantees
- Изменение лимитов размера/MIME на backend
- E2E Playwright обязательно (желательно smoke позже)

---

## 11. Decisions (закрытые Open Questions)

1. **Multi-file** — все подходящие до лимита экрана (Assumption 9).
2. **CapturePage** — вне MVP; это QR/камера для фото ДЗ, не конструктор (Assumption 11).
3. **Hint** — обязателен в UI (Assumption 10, US-CI-2b).

---

## 12. Suggested implementation order (после PLAN)

Не выполнять до approve spec + plan/tasks:

1. `lib/image-intake` + unit tests  
2. Wire `ContentBlocksEditor` (paste/DnD/display/hint) + component tests  
3. `StepView`  
4. `StepFeedbackForm` + preview size  
5. Docs cross-link from `teacher-cabinet-ux.md`
