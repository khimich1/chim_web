# Clipboard / DnD image intake

## Problem Statement
How might we дать учителю (и в смежных экранах с загрузкой картинок) вставлять изображение из буфера обмена или перетаскиванием в один жест, так чтобы оно читалось так же хорошо, как иллюстрации в тестах?

## Recommended Direction
**Направление A: shared intake + paste/DnD на контейнере редактора.**

Один клиентский механизм приёма файла (`paste` из clipboard, `drop`, file input) поверх существующего `uploadImage` → `/api/uploads/images`. Модель контента не меняется: отдельные блоки `text | image`.

Жесты вешаются на контейнер редактора (не только на textarea): картинка из буфера или drag-and-drop создаёт новый image-блок (после активного блока или в конец списка). File picker «+ Изображение» остаётся.

Отображение превью и показа ученику выровнять со стилем тестов (`CustomQuestionContent` / `QuestionContent`: `max-w-full`, без жёсткого мелкого `max-h` как у `ImageViewer`).

Порядок подключения экранов (один механизм, несколько срезов):
1. `ContentBlocksEditor` (темы: вопрос / эталон)
2. `StepView` (ответ картинкой в тесте)
3. `StepFeedbackForm` (фидбек к ДЗ)
4. `CapturePage` (фото ДЗ), по необходимости

## Key Assumptions to Validate
- [ ] Ctrl/Cmd+V со скриншотом в Chrome создаёт image-блок и не засоряет textarea текстом/filename
- [ ] Ширина контента «как в тестах» достаточна для превью; enlarge — [`image-lightbox-click-to-enlarge.md`](../specs/image-lightbox-click-to-enlarge.md)
- [ ] Те же жесты ожидаемы в фидбеке ДЗ и ответе в тесте (не только в конструкторе заданий)
- [ ] Desktop-first достаточно; на мобиле остаётся file picker / камера

## MVP Scope
**In**
- Shared helper/hook: извлечь `File` из `ClipboardEvent` / `DragEvent`, вызвать `uploadImage`
- Paste + DnD + file в `ContentBlocksEditor`
- Превью изображения в стиле тестов (читаемый размер)
- Vitest на paste/DnD → новый image-блок

**Next slices**
- Тот же intake в `StepView`, `StepFeedbackForm`, `CapturePage`

## Not Doing (and Why)
- Inline / rich-text картинки внутри текстового блока — ломает текущую модель блоков и API
- Lightbox / `ImageViewer` в превью — → [`image-lightbox-click-to-enlarge.md`](../specs/image-lightbox-click-to-enlarge.md) (supersedes «только если мелко»)
- Новый backend endpoint для paste — уже есть `/api/uploads/images`
- Mobile-first clipboard paste — desktop-first; мобильный UX через picker/камеру

## Open Questions
- Вставлять image-блок после *активного* текстового блока или всегда в конец списка?
- При paste картинки: полностью `preventDefault`, чтобы binary/filename не попадал в textarea?

## Context (codebase)
- Upload: `frontend/lib/api/uploads.ts` → `POST /api/uploads/images`
- Редактор блоков: `frontend/components/teacher/ContentBlocksEditor.tsx`
- Эталон отображения: `frontend/components/tests/CustomQuestionContent.tsx`
- Другие upload UI: `StepView.tsx`, `StepFeedbackForm.tsx`, `CapturePage.tsx`
