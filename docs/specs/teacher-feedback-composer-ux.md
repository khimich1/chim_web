# Spec: Teacher feedback composer UX

**Версия:** 0.1.0  
**Дата:** 2026-07-25  
**Статус:** IMPLEMENT — done  
**Источник:** [`docs/ideas/teacher-feedback-composer-ux.md`](../ideas/teacher-feedback-composer-ux.md)  
**Родитель:** [`SPEC.md`](../../SPEC.md) §1.9.9 (teacher review + QR + feedback)  
**Связано:**  
- [`clipboard-image-intake.md`](clipboard-image-intake.md) — paste/DnD уже в `StepFeedbackForm`  
- [`student-multi-photo-answer-paste.md`](student-multi-photo-answer-paste.md) — паритет QR / устройство / галерея  
- [`teacher-written-homework-review.md`](../ideas/teacher-written-homework-review.md) — базовый review flow  
**План:** [`tasks/teacher-feedback-composer-ux.md`](../../tasks/teacher-feedback-composer-ux.md)

---

## Assumptions (проверьте до PLAN)

Если не поправите — считаем принятыми:

1. **Composer UI** в `StepFeedbackForm` (и для per-step, и для общего комментария): один крупный выделенный textarea-лист; иконка **микрофона** на листе (не отдельная секция «Голосовой комментарий» / кнопка «Записать голос»); кнопка **«Сохранить»** (не «Сохранить разбор») — скруглённая, визуально жирнее, выровнена **вправо**.
2. **Фото intake** как у ученика в `StepView`: подсказка про буфер, кнопки «Сфотографировать с телефона» + «Прикрепить с этого устройства», QR-блок, галерея превью с удалением. Сырой `<input type="file">` без label-кнопки — убрать.
3. **Лимит фото** без изменений: **5** на форму разбора (`FEEDBACK_IMAGE_LIMIT`).
4. **QR и там и там:** handoff доступен и для разбора шага (`position`), и для общего комментария к сдаче (`position` отсутствует).
5. **Тот же URL съёмки:** `capture_url` = `/student/capture/{token}` (как сейчас). Отдельный `/teacher/capture/...` **не** делаем. CapturePage адаптирует копирайт по `purpose` в meta.
6. **Фото с телефона не публикует разбор.** Upload по QR → изображение попадает в **локальный draft** формы (превью); ученик видит его только после «Сохранить» через существующий `PUT .../feedback`.
7. **Галерея до Save:** можно проверить превью, удалить любое фото, добавить ещё (paste / устройство / новый QR), пока `< 5`.
8. **Handoff — отдельный purpose `feedback`**, не reuse student `answer` handoff as-is (иначе фото ушло бы в ответ ученика). Та же таблица/механизм токенов + та же capture-страница; внутри токена — тип и привязка к ДЗ.
9. **Модель токена (предложение):** расширить `UploadHandoffToken` (или эквивалент без новой таблицы URL):
   - `purpose`: `"answer"` | `"feedback"` (default `"answer"` для существующих строк)
   - для `feedback`: `homework_id` (FK), `teacher_id`, `position: int | null` (`null` = общий комментарий)
   - `session_id` / `student_id` для `feedback` — nullable **или** не используются (миграцией ослабить NOT NULL только для feedback-строк)
   - после `POST /api/capture/{token}`: `used_at` + **`staged_image_id`** (FK upload); **не** писать в `TestSessionStepFeedback` / `HomeworkSubmissionFeedback`
10. **Polling на ПК учителя:** как у ученика по смыслу — форма опрашивает статус токена (например `GET /api/capture/{token}`), пока `staged_image_id` не появится → append в локальный state → можно создать новый handoff для следующего фото. WebSocket не делаем.
11. **Auth на capture:** для `purpose=feedback` достаточно залогиненного **преподавателя-владельца** ДЗ (cookie). Чужой teacher / student → 403. Для `purpose=answer` поведение §1.9.9 без регрессий.
12. **Один QR = одно фото** (token одноразовый), как у ученика; следующее фото — новый «Сфотографировать с телефона».
13. **Голос:** клик по mic на листе открывает тот же flow записи (`VoiceRecorder`), но UI компактный (иконка + состояние recording/preview), без отдельного заголовка секции.
14. **Не трогаем в этом composer MVP:** layout `WrittenAnswerReview` (split фото|эталон), удаление блока «Общий комментарий», очередь сдач, annotate на фото ученика. Lightbox → [`image-lightbox-click-to-enlarge.md`](image-lightbox-click-to-enlarge.md) (supersedes прежнее «не трогаем lightbox»).
15. **Срезы поставки:**  
    (1) Composer UI + mic + «Сохранить» + intake кнопки (paste/устройство уже есть)  
    (2) Backend feedback-handoff + capture staging  
    (3) QR UI + polling в `StepFeedbackForm`  
    (4) CapturePage copy для feedback + тесты

→ Поправьте нумерованные пункты, иначе после approve идём в PLAN с ними.

---

## 1. Objective

### Что строим

Более интуитивную форму разбора письменного ДЗ у преподавателя: текстовый composer с микрофоном, понятная кнопка сохранения, прикрепление фото разбора так же, как ученик прикрепляет ответ (буфер / устройство / QR), с превью до публикации.

### Зачем

Сейчас в `StepFeedbackForm` три одинаковые секции («текст / голос / фото») и две копии формы на странице выглядят как дубль; голос — отдельная кнопка «Записать голос»; фото — сырой file picker. С телефона учитель не может снять фото-разбор так же удобно, как ученик — ответ.

### Для кого

| Роль | Эффект |
|------|--------|
| **Преподаватель** | Быстрее оставляет текст/голос/фото разбора; снимает пояснение с телефона по QR |
| **Ученик** | Без изменения контракта: видит разбор только после Save (как сейчас) |

### User stories + acceptance

| ID | Story | Acceptance |
|----|--------|------------|
| US-FC-1 | Как преподаватель, пишу разбор в крупном текстовом поле | Textarea визуально доминирует (лист); placeholder сохранён по смыслу |
| US-FC-2 | Как преподаватель, записываю голос с иконки микрофона на листе | Нет секции «Голосовой комментарий» / «Записать голос»; mic запускает запись; превью/удаление голоса доступны |
| US-FC-3 | Как преподаватель, сохраняю разбор кнопкой справа | Кнопка «Сохранить» (или «Сохранение…»), скруглённая, жирнее primary, `ml-auto` / flex end |
| US-FC-4 | Как преподаватель, прикрепляю фото с ПК | «Прикрепить с этого устройства» + paste/DnD → превью в галерее; лимит 5 |
| US-FC-5 | Как преподаватель, снимаю фото разбора с телефона по QR (шаг) | QR на per-step форме → `/student/capture/{token}` → фото в превью формы, **не** у ученика до Save |
| US-FC-6 | Как преподаватель, снимаю фото для общего комментария по QR | То же для блока без `position` |
| US-FC-7 | Как преподаватель, проверяю фото до отправки | Превью видно; «Удалить» убирает из draft; можно добавить ещё |
| US-FC-8 | Как преподаватель, жму «Сохранить» | `PUT` feedback с image ids; ученик видит фото в разборе; `has_teacher_feedback` как сейчас |
| US-FC-9 | Как система, student answer handoff не ломается | Существующие pytest handoff/capture зелёные; QR ученика по-прежнему пишет в `answer_image_ids` |

---

## 2. Tech Stack

| Слой | Стек |
|------|------|
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic v2 |
| Frontend | Next.js App Router, React client, `react-qr-code` (уже в проекте) |
| Upload | `POST /api/uploads/images` (device/paste); capture multipart для QR |
| Intake | `frontend/lib/image-intake.ts` |
| Tests | `pytest` (handoff/capture/feedback RBAC); Vitest + RTL (`StepFeedbackForm`, CapturePage) |

Новых npm/pip зависимостей **не требуется** (QR-lib уже есть).

---

## 3. Commands

```bash
# Backend
cd backend
source .venv/bin/activate
alembic upgrade head
pytest tests/test_upload_handoff.py tests/test_homework_feedback.py -q
pytest -q

# Frontend
cd frontend
npm run test -- --run components/homework/StepFeedbackForm
npm run test -- --run components/homework/CapturePage
npm run lint
npm run build
```

---

## 4. Project Structure (затрагиваемое)

```
backend/
  alembic/versions/           # purpose + feedback fields / staged_image_id
  app/models/upload_handoff_token.py
  app/repositories/app/upload_handoff_repo.py
  app/services/upload_handoff_service.py
  app/api/routers/            # homework feedback-handoff create; capture branch
  app/schemas/handoff.py
  tests/test_upload_handoff.py
  tests/…                     # feedback handoff RBAC

frontend/
  components/homework/StepFeedbackForm.tsx
  components/homework/VoiceRecorder.tsx   # compact / icon trigger
  components/homework/CapturePage.tsx     # copy by purpose
  lib/api/handoff.ts                      # createFeedbackHandoff + meta fields
  lib/api/homework-feedback.ts            # без смены PUT контракта, если не нужно
  components/homework/StepFeedbackForm.test.tsx
  components/homework/CapturePage.test.tsx
```

---

## 5. Code Style

Следовать существующим паттернам `StepView` (QR + polling) и `StepFeedbackForm` (draft state → PUT).

Пример контракта (ориентир, имена можно уточнить в PLAN):

```python
# POST /api/homework/{homework_id}/feedback-handoff
# body optional: { "position": 0 }  # omit/null → submission-level
class FeedbackHandoffCreate(BaseModel):
    position: int | None = None

class CaptureMetaResponse(BaseModel):
    purpose: Literal["answer", "feedback"]
    # answer: session_id, position, task_title, ...
    # feedback: homework_id, position: int | None, title hint
    expires_at: datetime
    staged_image_id: uuid.UUID | None = None
    staged_image_url: str | None = None
    already_has_photo: bool  # answer: step has photos; feedback: token already used
```

Frontend: после polling `staged_image_id` → `setImageIds` / `setImageUrls` локально; Save без изменений семантики `saveStepFeedback` / `saveSubmissionFeedback`.

---

## 6. Testing Strategy

| Уровень | Что |
|---------|-----|
| **pytest** | Create feedback handoff (step + submission); capture upload stages image, не пишет feedback; RBAC (other teacher 403); answer handoff regression; token reuse → 410 |
| **vitest** | Composer: mic visible, нет «Записать голос» label-секции; кнопка «Сохранить»; device upload → preview → remove; mock handoff → poll → preview |
| **CapturePage** | Meta `purpose=feedback` → другой заголовок/hint; upload success |
| **Ручной смоук** | QR с телефона → превью на ПК → удалить → снова QR → Save → ученик видит |

Coverage: новые ветки handoff + UI form; не гнаться за % ради %.

---

## 7. Boundaries

**Always**

- Хотя бы одно из text / voice / images при Save (как сейчас, 422 иначе)
- Feedback images MIME jpeg/png/webp; лимит 5
- Answer handoff и feedback handoff не смешивают целевые сущности
- Тесты зелёные до merge среза

**Ask first**

- Ломать NOT NULL на `session_id` у `UploadHandoffToken` vs отдельная таблица staging
- Менять TTL handoff (сейчас 15 мин)
- Менять лимит 5 фото feedback

**Never**

- Публиковать feedback ученику из `POST /api/capture`
- Отдельный `/teacher/capture` route в этом релизе
- Коммитить секреты / `.env`
- Менять статусы «принято / на доработку» (их нет и не добавляем)

---

## 8. API (дельта к §1.9.9)

| Method | Path | Role | Описание |
|--------|------|------|----------|
| POST | `/api/homework/{id}/feedback-handoff` | teacher | Создать QR-token (`purpose=feedback`); body `{ position?: number \| null }` |
| GET | `/api/capture/{token}` | auth по purpose | Meta + для feedback: `staged_image_id/url` после upload |
| POST | `/api/capture/{token}` | auth по purpose | Upload: answer → append answer images; feedback → stage image на токене |

`PUT` feedback endpoints **без изменения** семантики публикации.

Инвалидация: новый feedback-handoff для того же `(homework_id, position|null)` инвалидирует предыдущий unused token (зеркало student-step).

---

## 9. Success Criteria

- [x] US-FC-1…US-FC-9 выполнены (автотесты; ручной смоук — ниже)
- [x] На экране проверки нет «Записать голос» / «Сохранить разбор» как primary labels
- [x] QR на шаге и на общем комментарии; URL начинается с `/student/capture/`
- [x] До Save ученик не видит новые feedback-фото; после Save — видит (staging + PUT unchanged)
- [x] `pytest` + целевые `vitest` зелёные; student handoff без регрессий

---

## 10. Out of Scope

| Исключено | Почему |
|-----------|--------|
| `/teacher/capture/...` | Явно отвергнуто — не плодить сущности |
| Авто-PUT feedback при съёмке | Нужно превью/удаление до Save |
| Merge/удаление «Общего комментария» | Отдельная идея |
| Review cockpit / очередь сдач | Отдельная идея |
| Annotate / рисование на фото ученика | Вне job |
| Push/email о разборе | §1.9.9 |

---

## 11. Open Questions

Нет блокирующих после ответов 2026-07-25. Мелочи реализации (nullable FK vs check constraint) — решить в PLAN, не в UI-контракте.
