# Implementation Plan: Student multi-photo answer + clipboard paste

**Источник:** [`docs/specs/student-multi-photo-answer-paste.md`](../docs/specs/student-multi-photo-answer-paste.md) v0.1.0 · idea: [`docs/ideas/student-multi-photo-answer-paste.md`](../docs/ideas/student-multi-photo-answer-paste.md)  
**Дата плана:** 2026-07-24  
**Статус:** IMPLEMENT  
**Skills:** planning-and-task-breakdown → incremental-implementation → TDD  
**Коммиты:** только по явной просьбе пользователя

### Progress

| Task | Статус |
|------|--------|
| MP-1 Schema + migration + StepRead contract | ✅ |
| MP-2 Attach append / delete / compare+submit guards | ✅ |
| MP-3 Handoff append + RBAC array | ✅ |
| MP-4 Homework teacher detail multi URLs | ✅ |
| MP-5 StepView intake zone + gallery UI | ✅ |
| MP-6 Teacher review / submission photos UI | ✅ |
| MP-7 Docs cross-links (clipboard-image-intake) | ✅ |

---

## Overview

Заменить одно `answer_image_id` на массив до **3** id; paste/DnD на обёртке «ответ + фото» как в конструкторе; handoff и teacher review — все страницы. Вертикальные срезы: контракт → write-path → handoff/RBAC → teacher API → student UI → teacher UI → docs.

---

## Architecture Decisions

| Решение | Выбор | Почему |
|---------|--------|--------|
| Storage | JSON `answer_image_ids` + drop FK | Один SoT; FE/BE в одном релизе |
| Max | 3 | Product decision |
| Attach API | POST append одного id | Совместим с upload→attach flow |
| Remove | DELETE by image_id | Нужно до compare |
| Paste zone | Wrapper вокруг input+gallery+buttons | Как ContentBlocksEditor; чинит UX gap |
| Event multi | `limit = 3 - current.length` | Spec Assump. 8 |
| Handoff | Append until full | Spec Assump. 9 |
| Teacher UI | List/pager of URLs | Без нового lightbox в MVP |
| Singular API | Remove in same release | Нет zombie fields |

**ДОПУЩЕНИЯ:** см. Assumptions 1–15 в spec.  
→ Поправь сейчас, иначе после «ок / implement» идём с ними.

---

## Dependency graph

```
MP-1 migration + schemas (StepRead arrays)
        │
        ├── MP-2 attach append / delete / compare / submit
        │         │
        │         ├── MP-3 handoff + upload RBAC
        │         │         │
        │         └── MP-4 homework teacher detail URLs
        │                   │
        │                   └── Checkpoint A (API green)
        │
        ├── MP-5 StepView (needs MP-2 client API)
        └── MP-6 Teacher review UI (needs MP-4)
                  │
                  └── MP-7 docs
                            │
                            └── Checkpoint B
```

**Параллельно после Checkpoint A:** MP-5 и MP-6.

**Демо ученику:** MP-1…MP-3 + MP-5.  
**Демо учителю:** + MP-4 + MP-6.

---

## Task List

### Phase 1: Contract + write path

## Task MP-1: Schema migration + StepRead arrays

**Description:** Добавить `answer_image_ids` JSON, backfill из `answer_image_id`, drop старую колонку/FK/relationship. Обновить Pydantic `StepRead` → `answer_image_ids` + `answer_image_urls`. Обновить маппинг в exam/custom/homework adapters при чтении сессии.

**Acceptance criteria:**
- [ ] Alembic upgrade/downgrade
- [ ] Существующий шаг с одним фото → массив длины 1 после migrate
- [ ] `GET session` отдаёт массивы, без singular fields
- [ ] pytest на backfill + session read

**Verification:**
- [ ] `alembic upgrade head`
- [ ] `pytest tests/test_homework_written_photo.py -q` (обновить фикстуры/asserts)

**Dependencies:** None  

**Files likely touched:**
- `backend/alembic/versions/0xx_….py`
- `backend/app/models/test_session.py`
- `backend/app/schemas/test_session.py`
- `backend/app/services/test_session/*.py`
- `frontend/lib/api/types.ts` (синхронно или в MP-5)

**Estimated scope:** Large

---

## Task MP-2: Attach append, delete, compare/submit guards

**Description:** `attach_answer_image` append с лимитом 3 и анти-дублем; новый DELETE endpoint; compare/submit проверяют `len >= 1` в ДЗ. Response shape — полные массивы.

**Acceptance criteria:**
- [ ] 1→2→3 append OK; 4-й → 422
- [ ] DELETE до checked OK; после checked → 409
- [ ] Compare без фото в homework → 422
- [ ] pytest покрывает happy + limit + delete + compare

**Verification:**
- [ ] `pytest tests/test_homework_written_photo.py tests/test_test_session_content_self_check.py -q`

**Dependencies:** MP-1  

**Files likely touched:**
- `backend/app/api/routers/test_sessions.py`
- `backend/app/schemas/test_session.py`
- `backend/app/services/test_session/facade.py`
- `backend/app/services/test_session/custom_adapter.py`
- `backend/app/services/test_session/exam_adapter.py`
- `backend/app/services/homework_submit_service.py`
- `backend/tests/…`

**Estimated scope:** Large

---

## Checkpoint A prerequisites: MP-3 + MP-4

## Task MP-3: Handoff append + upload RBAC for arrays

**Description:** Handoff больше не «уже есть фото = блок»; append пока `<3`. RBAC `teacher_can_view_answer_image` / `student_can_view_image` ищут id в JSON-массиве (LIKE/`cast` как feedback images, или membership helper).

**Acceptance criteria:**
- [ ] Два capture подряд на шаг → 2 id
- [ ] Третий OK, четвёртый отказ
- [ ] Teacher/student GET своих answer photos → 200; чужой → 403
- [ ] pytest handoff + uploads RBAC

**Verification:**
- [ ] `pytest tests/test_upload_handoff.py tests/test_uploads_api.py -q` (доп. кейсы)

**Dependencies:** MP-2  

**Files likely touched:**
- `backend/app/services/upload_handoff_service.py`
- `backend/app/schemas/handoff.py`
- `backend/app/repositories/app/upload_repo.py`
- `backend/tests/test_upload_handoff.py`

**Estimated scope:** Medium

---

## Task MP-4: Homework teacher detail multi URLs

**Description:** `submission_steps` / homework detail отдают `answer_image_urls: string[]`. Обновить сервисы и тесты, убрать singular.

**Acceptance criteria:**
- [ ] Teacher GET homework после сдачи с 2 фото → массив длины 2
- [ ] pytest homework detail / written photo

**Verification:**
- [ ] `pytest tests/test_homework_written_photo.py tests/test_homework_feedback_api.py -q`

**Dependencies:** MP-2  

**Files likely touched:**
- `backend/app/schemas/homework.py`
- `backend/app/services/homework_service.py`
- `backend/app/services/test_session/homework_adapter.py`
- `backend/tests/…`

**Estimated scope:** Medium

---

### Checkpoint A: After MP-1…MP-4

- [x] `pytest` по written photo / handoff / uploads / homework detail зелёный
- [x] OpenAPI отражает arrays + DELETE
- [x] Нет ссылок на `answer_image_id` в backend read/write path (кроме миграции / attach request body)

---

### Phase 2: UI

## Task MP-5: StepView intake + gallery

**Description:** Обернуть «Ваш ответ» + галерея + кнопки в одну paste/DnD зону. State на массивах; attach append; delete; hint; `limit = 3 - length`. Обновить `lib/api/tests.ts` + types. Vitest: paste-from-input, truncate, remove.

**Acceptance criteria:**
- [ ] US-MP-1…US-MP-3 в unit/RTL
- [ ] После checked — нельзя добавить/удалить
- [ ] Статус «N из 3» или превью всех фото

**Verification:**
- [ ] `npm run test -- --run components/tests/StepView.test.tsx`

**Dependencies:** MP-2 (API client)  

**Files likely touched:**
- `frontend/components/tests/StepView.tsx`
- `frontend/components/tests/StepView.test.tsx`
- `frontend/lib/api/tests.ts`
- `frontend/lib/api/types.ts`
- `frontend/lib/api/handoff.ts` (если типы ответа)

**Estimated scope:** Large

---

## Task MP-6: Teacher review multi-photo UI

**Description:** `WrittenAnswerReview`, `HomeworkSubmissionPhotos`, при необходимости `ImageViewer` — рендер списка/пейджера по `answer_image_urls[]`.

**Acceptance criteria:**
- [ ] US-MP-6: 2–3 фото видны в review
- [ ] vitest обновлены

**Verification:**
- [ ] `npm run test -- --run components/homework/WrittenAnswerReview.test.tsx`
- [ ] `npm run test -- --run components/homework/HomeworkSubmissionPhotos.test.tsx`

**Dependencies:** MP-4  

**Files likely touched:**
- `frontend/components/homework/WrittenAnswerReview.tsx`
- `frontend/components/homework/HomeworkSubmissionPhotos.tsx`
- `frontend/components/homework/ImageViewer.tsx` (optional)
- corresponding `*.test.tsx`

**Estimated scope:** Medium

---

## Task MP-7: Docs cross-links

**Description:** В `clipboard-image-intake` spec пометить StepView limit=1 как superseded этим документом; при необходимости одна строка в `written-homework-photo-submit` idea Not Doing → struck.

**Acceptance criteria:**
- [ ] Ссылки двусторонние idea ↔ spec ↔ plan
- [ ] Clipboard spec не врёт про limit 1 как актуальный SoT

**Verification:** manual doc read  

**Dependencies:** MP-5 (логически после UI, можно раньше)  

**Files likely touched:**
- `docs/specs/clipboard-image-intake.md`
- `docs/ideas/written-homework-photo-submit.md` (optional note)

**Estimated scope:** Small

---

### Checkpoint B: Done

- [x] Success criteria spec §8
- [x] Full relevant pytest + vitest green
- [ ] Manual: paste in answer field; 2× QR; teacher sees both

---

## Risks

| Risk | Mitigation |
|------|------------|
| Широкий blast radius singular→array | Один релиз FE+BE; grep `answer_image_id` / `answer_image_url` |
| SQLite JSON membership в RBAC | Тот же `cast(…, String).like` паттерн, что feedback ids; тесты |
| Handoff UI «уже есть фото» | Переписать на «N/3» / disable только при N==3 |
| Большой diff StepView | Сначала API client + state arrays, потом paste wrapper |

---

## Out of plan

- Reorder, PDF, stitch, limit≠3, CapturePage paste editor, lightbox
