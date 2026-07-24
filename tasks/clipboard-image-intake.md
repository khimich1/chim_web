# Implementation Plan: Clipboard / DnD image intake

**Источник:** [`docs/specs/clipboard-image-intake.md`](../docs/specs/clipboard-image-intake.md) v0.1.1 · idea: [`docs/ideas/clipboard-image-intake.md`](../docs/ideas/clipboard-image-intake.md)  
**Дата плана:** 2026-07-24  
**Статус:** ✅ IMPLEMENT complete (CI-1…CI-5) — commits по просьбе пользователя  
**Skills:** planning-and-task-breakdown → incremental-implementation → TDD  
**Коммиты:** только по явной просьбе пользователя

### Progress

| Task | Статус |
|------|--------|
| CI-1 `lib/image-intake` + unit tests | ✅ |
| CI-2 `ContentBlocksEditor` paste/DnD/display/hint | ✅ |
| CI-3 `StepView` intake | ✅ |
| CI-4 `StepFeedbackForm` intake + large preview | ✅ |
| CI-5 Docs cross-link `teacher-cabinet-ux` | ✅ |

---

## Overview

Единый frontend image intake: Ctrl/Cmd+V, drag-and-drop и file picker → существующий `uploadImage`. Сначала конструктор блоков (`ContentBlocksEditor`) с крупным превью «как в тестах» и hint; затем StepView и StepFeedbackForm. Backend и CapturePage не трогаем.

---

## Architecture Decisions

| Решение | Выбор | Почему |
|---------|--------|--------|
| Shared code | Чистые функции в `frontend/lib/image-intake.ts` | Нет `hooks/` в репо; легко unit-тестить; handlers тонкие в компонентах |
| Multi extract | `imageFilesFromDataTransfer(dt, { limit })` → `File[]` | Spec: multi до лимита экрана |
| Insert position | После `activeBlockIndex` (focus textarea), иначе append | Spec Assumption 2 |
| Paste guard | `preventDefault` только если есть allowed image | Text paste в textarea не ломается |
| Preview | `AuthenticatedImage` + классы эталона тестов | Убрать дубль `BlockImagePreview`; единый визуальный контракт |
| Upload | Последовательный `await uploadImage` по файлам | Проще ошибки/state, чем parallel race в onChange |
| Hook | Не вводим `useImageIntake` в MVP | Три экрана — копипаста handlers ок; вынести при боли |
| CapturePage | Вне плана | Spec Assumption 11 |

**ДОПУЩЕНИЯ (из spec, приняты для IMPLEMENT):**
1. Только frontend  
2. Insert after active / else end  
3. preventDefault только на image paste  
4. MIME jpeg/png/webp  
5. Display как в тестах, без lightbox  
6. Feedback preview ≥ ~16rem max-h / full width contain  
7. Лимиты: editor 10/event, feedback 5 total, StepView 1  
8. Hint обязателен на каждой зоне  
9. Desktop-first  

→ Поправь сейчас, иначе после «ок / implement» идём с этим.

---

## Dependency graph

```
CI-1 lib/image-intake (+ unit tests)
        │
        ├── CI-2 ContentBlocksEditor (paste/DnD/hint/display)  ← вертикальный демо-срез
        │         │
        │         └── Checkpoint A
        │
        ├── CI-3 StepView (parallel-ready after CI-1; after CI-2 preferred)
        └── CI-4 StepFeedbackForm
                  │
                  └── CI-5 docs cross-link
                            │
                            └── Checkpoint B (done)
```

**Минимум для демо учителю:** CI-1 + CI-2.

**Параллельно после CI-1:** CI-3 и CI-4 независимы друг от друга.

---

## Task List

### Phase 1: Foundation + конструктор

---

## Task CI-1: `lib/image-intake` + unit tests

**Description:** Чистые хелперы: allowlist MIME, извлечение `File[]` из `DataTransfer` (clipboard/drag), обрезка по `limit`, флаг «были отброшены лишние». TDD: сначала тесты.

**Acceptance criteria:**
- [ ] `isAllowedImageMime` / `isAllowedImageFile` — jpeg/png/webp ok; gif/pdf/empty — false
- [ ] `imageFilesFromDataTransfer(dt, { limit: N })` возвращает до N allowed files в порядке items/files
- [ ] При >N allowed → массив длины N + `truncated: true` (или отдельный return shape)
- [ ] Нет image → пустой массив / null-path без throw
- [ ] Экспорт константы display class или `CONTENT_IMAGE_CLASS` для UI (опционально здесь или в CI-2)

**Verification:**
- [ ] `cd frontend && npm run test -- image-intake`

**Dependencies:** None

**Files likely touched:**
- `frontend/lib/image-intake.ts` (NEW)
- `frontend/lib/image-intake.test.ts` (NEW)

**Estimated scope:** S

---

## Task CI-2: ContentBlocksEditor — paste / DnD / hint / display

**Description:** Подключить intake к редактору блоков: зона с `onPaste` / `onDragOver` / `onDrop`, sequential upload, insert после активного блока, hint, превью через `AuthenticatedImage` с классами как в тестах. File picker оставить.

**Acceptance criteria:**
- [ ] Paste image → `uploadImage` → image-блок(и) в onChange; text-only paste не preventDefault
- [ ] Drop 1..10 → до 10 блоков; >10 → сообщение про лимит
- [ ] Видимый hint про Ctrl+V / перетаскивание
- [ ] Превью: `max-w-full` / `object-contain` (не мелкий thumb); `BlockImagePreview` убран или сведён к AuthenticatedImage
- [ ] Во время upload повторный paste/drop disabled или игнорируется
- [ ] Vitest: mock upload + fire paste/drop

**Verification:**
- [ ] `npm run test -- ContentBlocksEditor`
- [ ] Manual (Chrome): PrintScreen → Ctrl+V в `/teacher/themes/...` новое задание; text paste в textarea; DnD PNG

**Dependencies:** CI-1

**Files likely touched:**
- `frontend/components/teacher/ContentBlocksEditor.tsx`
- `frontend/components/teacher/ContentBlocksEditor.test.tsx` (NEW)

**Estimated scope:** M

---

### Checkpoint A (после CI-1–CI-2)

- [x] Vitest image-intake + ContentBlocksEditor зелёные
- [ ] Ручной paste/DnD в конструкторе работает
- [x] Превью читаемое
- [x] Review с человеком перед CI-3/CI-4 (опционально — можно сразу)

---

### Phase 2: Остальные экраны + docs

---

## Task CI-3: StepView — paste / DnD ответа-картинки

**Description:** На зоне загрузки ответа-изображения: paste/DnD → существующий `handleAnswerImageUpload`. Лимит 1: при нескольких файлах — первый. Hint.

**Acceptance criteria:**
- [ ] Paste/drop image → тот же путь, что file input (`uploadImage` + `attachAnswerImage`)
- [ ] Multi → только первый файл
- [ ] Hint виден рядом с зоной
- [ ] Text paste в поле текстового ответа не ломается (если handlers на общем предке — только image path preventDefault)

**Verification:**
- [ ] `npm run test -- StepView` (добавить/расширить кейсы paste при наличии тестовой обвязки; иначе manual)
- [ ] Manual: шаг с image-ответом → Ctrl+V / drop

**Dependencies:** CI-1 (желательно после Checkpoint A)

**Files likely touched:**
- `frontend/components/tests/StepView.tsx`
- `frontend/components/tests/StepView.test.tsx` (если уже есть — расширить)

**Estimated scope:** M

---

## Task CI-4: StepFeedbackForm — intake + крупное превью

**Description:** Paste/DnD до лимита 5 фото; увеличить превью (убрать `h-20 w-20 object-cover`); hint.

**Acceptance criteria:**
- [ ] Paste/drop добавляет фото, пока `imageIds.length < 5`
- [ ] Multi-drop заполняет оставшиеся слоты
- [ ] При 5 — intake disabled / сообщение
- [ ] Превью читаемое (`object-contain`, max-w-full или max-h ≥ 16rem)
- [ ] Vitest: mock upload + paste/limit (расширить существующий тест)

**Verification:**
- [ ] `npm run test -- StepFeedbackForm`
- [ ] Manual: разбор ДЗ → Ctrl+V / drop, проверить размер превью

**Dependencies:** CI-1

**Files likely touched:**
- `frontend/components/homework/StepFeedbackForm.tsx`
- `frontend/components/homework/StepFeedbackForm.test.tsx`

**Estimated scope:** M

---

## Task CI-5: Docs — cross-link teacher-cabinet-ux

**Description:** В `teacher-cabinet-ux.md` у US-TC-3 / § media указать, что детали intake = `clipboard-image-intake.md`; lightbox по-прежнему отдельный.

**Acceptance criteria:**
- [ ] Ссылка на spec intake в teacher-cabinet-ux
- [ ] Статус этого plan/spec обновлён после merge работы (при закрытии)

**Verification:**
- [ ] Markdown links resolve

**Dependencies:** None (можно после CI-2)

**Files likely touched:**
- `docs/specs/teacher-cabinet-ux.md`
- `docs/specs/clipboard-image-intake.md` (статус → approved / implementing)

**Estimated scope:** XS

---

### Checkpoint B (complete)

- [x] Все AC из spec §9 закрыты (кроме CapturePage — N/A)
- [x] `npm run test` по затронутым сюитам зелёный
- [x] Backend не изменён
- [ ] Ready for code review / commit по просьбе

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Paste на bubble к document vs контейнер | Med | Зона editor с focus; тестировать фокус в textarea |
| Safari clipboard image quirks | Low (desktop Chrome primary) | Document; file picker остаётся |
| Sequential multi-upload медленный | Low | 10 max; show uploading state |
| StepView сложный setup для vitest | Med | Helper unit + manual; минимальный component test |
| Регрессия text paste | High | Явный тест «text paste не вызывает upload» |

---

## Out of scope (напоминание)

- CapturePage  
- Lightbox / ImageViewer  
- Rich-text inline images  
- Backend MIME/size changes  
- Новые npm deps  

---

## Open Questions

Нет блокирующих. При IMPLEMENT уточнять только если всплывёт UX paste-фокуса.

---

## Next step

После approve плана: **IMPLEMENT с CI-1 (TDD)** → CI-2 → Checkpoint A → CI-3/CI-4 → CI-5.
