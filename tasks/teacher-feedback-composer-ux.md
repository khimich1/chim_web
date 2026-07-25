# Implementation Plan: Teacher feedback composer UX

**Источник:** [`docs/specs/teacher-feedback-composer-ux.md`](../docs/specs/teacher-feedback-composer-ux.md) v0.1.0 · idea: [`docs/ideas/teacher-feedback-composer-ux.md`](../docs/ideas/teacher-feedback-composer-ux.md)  
**Дата плана:** 2026-07-25  
**Статус:** IMPLEMENT — done  
**Skills:** planning-and-task-breakdown → incremental-implementation → TDD  
**Коммиты:** только по явной просьбе пользователя

### Progress

| Task | Статус |
|------|--------|
| FC-1 VoiceRecorder compact mic | ✅ |
| FC-2 Composer sheet + Save + device intake | ✅ |
| FC-3 Model + migration handoff feedback fields | ✅ |
| FC-4 Repo + schemas feedback handoff / capture | ✅ |
| FC-5 Service + router create + capture stage/RBAC | ✅ |
| FC-6 Frontend API client (feedback handoff + meta) | ✅ |
| FC-7 StepFeedbackForm QR + polling | ✅ |
| FC-8 CapturePage purpose=feedback copy | ✅ |
| FC-9 Vitest CapturePage + StepFeedbackForm QR + docs | ✅ |

---

## Overview

Сделать форму разбора письменного ДЗ (`StepFeedbackForm`) похожей на понятный composer: крупный textarea-лист с mic, кнопка «Сохранить» справа, фото-intake как у ученика в `StepView` (буфер / устройство / QR). QR идёт на тот же `/student/capture/{token}`; upload с телефона **стейджит** фото в токен (`purpose=feedback`), а в разбор ученика попадает только после существующего `PUT .../feedback`. Порядок — по срезам спеки: UI → backend handoff → QR/polling → CapturePage + тесты.

---

## Architecture Decisions

| Решение | Выбор | Почему |
|---------|--------|--------|
| Storage токена | Расширить `UploadHandoffToken`, без новой таблицы | Spec Assump. 8–9; один URL capture; меньше сущностей |
| `purpose` | `"answer"` \| `"feedback"`, default `"answer"` | Backfill существующих строк; answer path без смены семантики |
| FK для feedback | `homework_id` + `teacher_id`; `session_id` / `student_id` nullable; `position` nullable (`null` = submission-level) | Spec Assump. 9; check constraint / app-level guard: answer требует session+student+position; feedback — homework+teacher |
| Staging | `staged_image_id` FK → `uploaded_images`; **не** писать в feedback tables на capture | Фото в draft формы до Save |
| GET после upload (feedback) | Для `purpose=feedback` GET **разрешён** после `used_at`, отдаёт `staged_image_id` / url; POST reuse → 410 | Spec: poll GET until staged; иначе polling ломается (сейчас `_require_active_token` 410 на used) |
| Answer GET/POST | Без регрессий: GET только active unused; POST append answer images | US-FC-9 |
| Capture auth | Feedback: cookie + teacher-владелец homework → иначе 403; Answer: как сейчас (token in URL, без login на API) | Spec Assump. 11; CapturePage уже зовёт `getMe` для UI login |
| Meta/Upload schemas | Один `CaptureMetaResponse` с `purpose` + optional answer/feedback fields; upload response с `purpose` + answer arrays **или** staged id | FE ветвится по `purpose`; OpenAPI один контракт |
| Create endpoint | `POST /api/homework/{assignment_id}/feedback-handoff` body `{ position?: number \| null }` | Имя `assignment_id` как в существующем homework router; path из спеки |
| Invalidate | Новый unused feedback-token для `(homework_id, position IS NOT DISTINCT FROM …)` инвалидирует предыдущий | Зеркало student-step; учесть SQL NULL |
| Polling FE | `GET /api/capture/{token}` ~2.5s → append `staged_image_id` в local `imageIds`/`imageUrls` | Не `getSession` (как StepView) — feedback не в session step |
| PUT feedback | Без смены семантики | US-FC-8 |
| VoiceRecorder | Prop `variant="button" \| "icon"` (или `trigger="mic"`); default button | Не форкать компонент; StepFeedbackForm → icon |
| Capture route | Только `/student/capture/{token}` | Spec Assump. 5 / Never |
| Scope UI | Только `StepFeedbackForm` (+ VoiceRecorder/CapturePage); `WrittenAnswerReview` layout не трогать | Spec Assump. 14 |

**As-is (проверено в коде):**

- `UploadHandoffToken`: `session_id`, `position`, `student_id` все NOT NULL; нет `purpose` / staging.
- Capture router: **без** user auth — только token.
- StepView polls `getSession` после create handoff; feedback должен poll capture meta.
- `StepFeedbackForm`: секции «Голосовой комментарий» / сырой `<input type="file">` / «Сохранить разбор»; paste/DnD уже есть (`FEEDBACK_IMAGE_LIMIT = 5`).
- `VoiceRecorder`: кнопка «Записать голос».
- Homework feedback: `PUT .../steps/{position}/feedback`, `PUT .../submission-feedback`.

**ДОПУЩЕНИЯ (из spec, приняты для IMPLEMENT после approve):**
1. Composer + mic + «Сохранить» справа в `StepFeedbackForm` (step + submission).
2. Intake как StepView; сырой file input убрать.
3. Лимит 5.
4. QR и на шаге, и на общем комментарии.
5. Тот же `/student/capture/{token}`.
6. Capture не публикует feedback.
7. Галерея до Save: preview / delete / add.
8. `purpose=feedback`, не reuse answer as-is.
9. Модель токена — расширение таблицы + staging FK.
10. Polling GET capture (не WebSocket).
11. Auth teacher-owner для feedback capture.
12. Один QR = одно фото.
13. Mic на листе → тот же VoiceRecorder flow, компактный UI.
14. Не трогать WrittenAnswerReview layout / очередь / annotate.
15. Срезы поставки 1→4 как phases ниже.

→ Поправь сейчас, иначе после «ок / implement» идём с этим.

---

## Dependency graph

```
FC-1 VoiceRecorder icon variant
        │
        └── FC-2 Composer + Save + device buttons (+ vitest UI)
                  │
                  └── Checkpoint A (UI без QR)

FC-3 migration + ORM
        │
        └── FC-4 repo + Pydantic schemas
                  │
                  └── FC-5 service + router + pytest handoff/RBAC
                            │
                            └── Checkpoint B (API green)

FC-6 FE handoff client types          ← after FC-5 (contract)
        │
        └── FC-7 StepFeedbackForm QR + polling (+ vitest)
                  │
                  ├── FC-8 CapturePage feedback copy
                  │         │
                  └── FC-9 CapturePage + form QR tests + docs cross-link
                            │
                            └── Checkpoint C (E2E smoke ready)
```

**Параллельно после Checkpoint B:** FC-6 затем FC-7; FC-8 можно начать сразу после FC-6 (meta `purpose`), параллельно с FC-7.

**Демо учителю без телефона:** FC-1 + FC-2.  
**Демо с QR:** + FC-3…FC-8.

**Порядок срезов спеки:** Phase 1 = slice 1; Phase 2 = slice 2; Phase 3 = slice 3; Phase 4 = slice 4. Backend после UI — fail-fast на UX без блокировки; контракт handoff — следующий high-risk кусок.

---

## Task List

### Phase 1: Composer UI (spec slice 1)

---

## Task FC-1: VoiceRecorder — compact mic trigger

**Description:** Добавить компактный режим запуска записи (иконка микрофона + aria-label), без текста «Записать голос» как primary CTA. Сохранить recording / preview / confirm / discard flow. Default — текущая кнопка (регрессий в других местах нет, если VoiceRecorder используется только из feedback — проверить grep).

**Acceptance criteria:**
- [x] `variant="icon"` (или эквивалент): mic control; нет видимого label «Записать голос»
- [x] `variant="button"` (default): поведение как сейчас
- [x] Recording / preview / «Использовать» / «Перезаписать» работают в icon-режиме
- [x] Vitest: icon mode не рендерит «Записать голос»; start recording reachable

**Verification:**
- [x] `cd frontend && npm run test -- --run components/homework/VoiceRecorder` (или рядом с StepFeedbackForm, если отдельного файла тестов нет — добавить минимальный)

**Dependencies:** None

**Files likely touched:**
- `frontend/components/homework/VoiceRecorder.tsx`
- `frontend/components/homework/VoiceRecorder.test.tsx` (NEW или расширить существующий)

**Estimated scope:** S

---

## Task FC-2: StepFeedbackForm composer + Save + device intake

**Description:** Редизайн формы: крупный выделенный textarea-лист; mic (`VoiceRecorder` icon) на листе; убрать секции «Текстовый комментарий» / «Голосовой комментарий» как отдельные заголовки (placeholder по смыслу сохранить); кнопка «Сохранить» / «Сохранение…» — скруглённая, жирнее primary, выровнена вправо (`ml-auto` / flex end). Фото: hint про буфер; кнопка «Прикрепить с этого устройства» как label+sr-only input (паттерн StepView); сырой видимый `<input type="file">` убрать. Paste/DnD/галерея/лимит 5 без смены логики upload. QR **ещё нет** (Phase 3).

**Acceptance criteria:**
- [x] Textarea визуально доминирует (лист)
- [x] Нет primary labels «Голосовой комментарий» / «Записать голос» / «Сохранить разбор»
- [x] Кнопка «Сохранить» справа; disabled-семантика как сейчас (`hasContent`, uploads)
- [x] Device button + paste/DnD → preview → remove; лимит 5
- [x] Vitest: Save label, mic present, device upload → preview → remove

**Verification:**
- [x] `cd frontend && npm run test -- --run components/homework/StepFeedbackForm`
- [x] `npm run lint`

**Dependencies:** FC-1

**Files likely touched:**
- `frontend/components/homework/StepFeedbackForm.tsx`
- `frontend/components/homework/StepFeedbackForm.test.tsx`

**Estimated scope:** M

---

## Checkpoint A: After FC-1…FC-2

- [x] Vitest StepFeedbackForm + VoiceRecorder зелёные
- [ ] Ручной смоук: review page — composer, mic, Save справа, device/paste preview
- [x] QR ещё отсутствует — ок
- [ ] Review с human перед backend (если нужны правки visual weight)

---

### Phase 2: Backend feedback-handoff + staging (spec slice 2)

---

## Task FC-3: Alembic + ORM — purpose / feedback FKs / staged_image_id

**Description:** Миграция `upload_handoff_tokens`: `purpose` (string/enum, default `answer`); для feedback — `homework_id`, `teacher_id`, `staged_image_id` (nullable FK); ослабить NOT NULL на `session_id` / `student_id`; `position` nullable. Check constraint (или документированный app-level + pytest): answer ↔ session+student+position; feedback ↔ homework+teacher. Downgrade обязателен.

**Acceptance criteria:**
- [x] `alembic upgrade head` / `downgrade -1` на чистой БД
- [x] Существующие answer-токены после migrate: `purpose=answer`, FKs заполнены
- [x] ORM отражает новые поля; relationships при необходимости

**Verification:**
- [x] `cd backend && source .venv/bin/activate && alembic upgrade head`
- [x] `pytest tests/test_models.py -q` (если покрывает handoff) или smoke import model

**Dependencies:** None (параллельно Phase 1 после approve)

**Files likely touched:**
- `backend/alembic/versions/*_handoff_feedback_purpose.py` (NEW)
- `backend/app/models/upload_handoff_token.py`

**Estimated scope:** M

---

## Task FC-4: Repo + Pydantic schemas

**Description:** Repo: `create` для answer (как сейчас) и для feedback (`purpose`, homework/teacher/position null-ok, session/student null); `invalidate_unused_for_feedback(homework_id, position)`; `mark_used` + set `staged_image_id`. Schemas: `FeedbackHandoffCreate`, расширенный `CaptureMetaResponse` (`purpose`, optional answer fields, `homework_id`, `position: int | null`, `staged_image_id/url`, `already_has_photo` семантика по purpose), `CaptureUploadResponse` с веткой feedback (staged ids) без ломки answer clients — optional fields + `purpose`.

**Acceptance criteria:**
- [x] Repo create feedback row без session_id
- [x] Invalidate unused для того же homework+position (включая `position is NULL`)
- [x] OpenAPI-схемы отражают новые поля; answer-required fields остаются для answer responses

**Verification:**
- [x] Unit/repo tests или покрытие в FC-5 pytest (минимум — схемы импортируются)
- [ ] Ручная сверка `/docs` после FC-5

**Dependencies:** FC-3

**Files likely touched:**
- `backend/app/repositories/app/upload_handoff_repo.py`
- `backend/app/schemas/handoff.py`

**Estimated scope:** M

---

## Task FC-5: Service + router — create feedback-handoff, capture stage, RBAC

**Description:** `UploadHandoffService.create_feedback_handoff(teacher, homework_id, position)` — ownership homework, invalidate previous, TTL 15 мин, `capture_url` = `{frontend}/student/capture/{token}`. `get_capture_meta` / `capture_upload` ветвятся по `purpose`: answer — текущая логика; feedback — stage image на токене (`used_at` + `staged_image_id`), **не** upsert feedback tables; GET feedback после used отдаёт staged fields. Router: `POST /api/homework/{assignment_id}/feedback-handoff` (TeacherUser); capture GET/POST для feedback требуют teacher-owner (dependency/service check); student / other teacher → 403. Answer path без login-требования на capture API. Pytest: create step + submission; stage not publish; RBAC; answer regression; token reuse 410 on POST.

**Acceptance criteria:**
- [x] Create handoff step (`position=0`) и submission (`position` omit/null) → token + capture_url
- [x] POST capture feedback → image uploaded + staged on token; feedback tables пусты до PUT
- [x] Poll GET после upload → `staged_image_id` / url
- [x] Other teacher / student на feedback capture → 403
- [x] Answer handoff create/meta/upload pytest зелёные
- [x] Second POST same token → 410

**Verification:**
- [x] `pytest tests/test_upload_handoff.py tests/test_homework_feedback_api.py tests/test_feedback_handoff.py -q`
- [x] При необходимости новый `tests/test_feedback_handoff.py` — включить в команду выше

**Dependencies:** FC-4

**Files likely touched:**
- `backend/app/services/upload_handoff_service.py`
- `backend/app/api/routers/homework.py` (или capture deps)
- `backend/app/api/routers/capture.py`
- `backend/app/api/deps.py` (если нужен optional/current user на capture)
- `backend/tests/test_upload_handoff.py` и/или `backend/tests/test_feedback_handoff.py` (NEW)

**Estimated scope:** M

---

## Checkpoint B: After FC-3…FC-5

- [x] `alembic upgrade head` ок
- [x] `pytest tests/test_upload_handoff.py tests/test_homework_feedback_api.py tests/test_feedback_handoff.py -q` зелёные
- [ ] Ручной curl/OpenAPI: create feedback-handoff → capture upload → GET staged; PUT feedback по-прежнему публикует
- [ ] Review contract с human перед FE wiring (имена полей meta)

---

### Phase 3: QR UI + polling (spec slice 3)

---

## Task FC-6: Frontend API — `createFeedbackHandoff` + capture types

**Description:** Расширить `frontend/lib/api/handoff.ts`: `createFeedbackHandoff(assignmentId, position?: number | null)`; типы `CaptureMetaResponse` / upload с `purpose` и optional staged/answer fields. Не ломать `createHandoff` для StepView.

**Acceptance criteria:**
- [x] POST на `/api/homework/{id}/feedback-handoff` с/без position
- [x] `getCaptureMeta` типизирует `purpose` + `staged_image_id`
- [x] Существующие StepView imports компилируются

**Verification:**
- [x] `cd frontend && npm run build` — зелёный
- [x] Существующие handoff-related vitest всё ещё зелёные после FC-7/9

**Dependencies:** FC-5

**Files likely touched:**
- `frontend/lib/api/handoff.ts`
- опционально `frontend/lib/api/schema.d.ts` (если регенят OpenAPI в этом срезе — иначе вручную типы в handoff.ts)

**Estimated scope:** S

---

## Task FC-7: StepFeedbackForm — QR button + poll staged → gallery

**Description:** По образцу StepView: «Сфотографировать с телефона» → `createFeedbackHandoff(homeworkId, position)`; показать `react-qr-code` + hint; poll `getCaptureMeta` ~2.5s пока нет `staged_image_id`, затем append в local `imageIds`/`imageUrls`, сбросить QR, разрешить новый handoff пока `< 5`. Работает и при `position` undefined (submission). Не вызывать PUT до Save. Disable QR при лимите / uploading / saving.

**Acceptance criteria:**
- [x] QR URL содержит `/student/capture/`
- [x] Mock poll → preview в галерее без Save
- [x] Remove staged photo из draft; повторный QR возможен
- [x] Per-step и submission forms (оба instance `StepFeedbackForm`)
- [x] Vitest: create handoff + poll staged → preview

**Verification:**
- [x] `cd frontend && npm run test -- --run components/homework/StepFeedbackForm`

**Dependencies:** FC-2, FC-6

**Files likely touched:**
- `frontend/components/homework/StepFeedbackForm.tsx`
- `frontend/components/homework/StepFeedbackForm.test.tsx`
- возможно props: нужен `homeworkId` / `assignmentId` — проверить `WrittenAnswerReview` / callers (минимальный prop pass-through)

**Estimated scope:** M

---

## Checkpoint C prerequisites: Phase 4 in flight

(После FC-7 UI QR готов; CapturePage copy — следующий срез.)

---

### Phase 4: CapturePage copy + tests (spec slice 4)

---

## Task FC-8: CapturePage — copy / success path for `purpose=feedback`

**Description:** Ветвить UI по `meta.purpose`: для feedback — заголовок/hint про фото **разбора** (не ответ ученика); checklist/upload UX сохранить. Учесть upload response shape (staged vs answer arrays) без регрессии student answer success screen. Auth UX: teacher must be logged in (существующий `getMe` / login link); не добавлять `/teacher/capture`.

**Acceptance criteria:**
- [x] `purpose=feedback` → отличный заголовок/hint от answer
- [x] Upload success для feedback (не ожидает только `answer_image_ids`)
- [x] `purpose=answer` (или отсутствие purpose в старых mock) — без регрессии copy/flow

**Verification:**
- [x] `cd frontend && npm run test -- --run components/homework/CapturePage`

**Dependencies:** FC-6

**Files likely touched:**
- `frontend/components/homework/CapturePage.tsx`
- `frontend/components/homework/CapturePage.test.tsx`

**Estimated scope:** M

---

## Task FC-9: Integration vitest polish + docs cross-link

**Description:** Добить покрытие: CapturePage feedback meta; StepFeedbackForm QR+poll если не полностью в FC-7; regression answer CapturePage labels. Короткий cross-link в idea/spec plan path уже будет; при необходимости — строка в `docs/ideas/teacher-written-homework-review.md` или clipboard spec «см. teacher feedback composer». Не раздувать docs.

**Acceptance criteria:**
- [x] Vitest CapturePage + StepFeedbackForm зелёные
- [x] `npm run lint` / `npm run build` frontend
- [x] Backend full targeted pytest suite из спеки зелёный
- [x] Docs: plan linked from spec (уже); optional related idea link

**Verification:**
- [x] `cd frontend && npm run test -- --run components/homework/StepFeedbackForm components/homework/CapturePage && npm run lint && npm run build`
- [x] `cd backend && pytest tests/test_upload_handoff.py tests/test_homework_feedback_api.py tests/test_feedback_handoff.py -q`

**Dependencies:** FC-7, FC-8

**Files likely touched:**
- `frontend/components/homework/CapturePage.test.tsx`
- `frontend/components/homework/StepFeedbackForm.test.tsx`
- возможно `docs/ideas/teacher-written-homework-review.md` (одна ссылка)

**Estimated scope:** S

---

## Checkpoint C: Complete

- [x] US-FC-1…US-FC-9 закрыты (автотесты)
- [ ] Ручной смоук: QR с телефона → превью на ПК → удалить → снова QR → Save → ученик видит
- [ ] Student answer QR без регрессий
- [ ] Ready for code-review-and-quality

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| GET 410 after `used_at` ломает teacher polling | High | Explicit feedback branch: GET allowed when used + return staged; pytest |
| Nullable `session_id` ломает answer invariants / orphans | High | Check constraint + default purpose=answer; pytest create answer still NOT NULL |
| Capture auth change accidentally requires login for answer | High | Branch only `purpose=feedback`; answer tests without teacher cookie |
| `CaptureMetaResponse` breaking FE StepView/CapturePage | Med | Optional new fields; `purpose` default `"answer"` in responses |
| `position IS NULL` invalidate SQL wrong (NULL ≠ NULL) | Med | Use `IS NOT DISTINCT FROM` / `(position = :p) OR (:p IS NULL AND position IS NULL)` + pytest |
| Prop `homeworkId` missing on StepFeedbackForm callers | Med | Grep callers in FC-7; minimal prop drill from WrittenAnswerReview |
| VoiceRecorder icon a11y unclear | Low | `aria-label="Записать голос"` на icon; visible section title не возвращать |
| Scope creep into WrittenAnswerReview layout | Low | Spec Never; checklist «не трогал» |

---

## Open Questions

Нет блокирующих (spec §11). Решено в PLAN:

1. **Nullable FK vs отдельная таблица** → расширяем `UploadHandoffToken` + check constraint.  
2. **GET after used for feedback** → разрешён, отдаёт staging (иначе poll невозможен).  
3. **Path param name** → `assignment_id` в FastAPI router, URL `/api/homework/{assignment_id}/feedback-handoff`.

Неблокирующие (можно уточнить на Checkpoint B): точные русские строки CapturePage для feedback; визуальный weight кнопки Save (класс vs inline).

---

## Parallelization Opportunities

| После | Можно параллельно |
|-------|-------------------|
| Approve | Phase 1 (FC-1…2) ∥ Phase 2 start (FC-3) |
| Checkpoint B | FC-6 → затем FC-7 ∥ FC-8 |
| FC-7+FC-8 | FC-9 |

Must sequential: FC-3 → FC-4 → FC-5 → FC-6 → FC-7.
