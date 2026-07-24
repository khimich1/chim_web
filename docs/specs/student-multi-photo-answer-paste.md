# Spec: Student multi-photo answer + clipboard paste

**Версия:** 0.1.0  
**Дата:** 2026-07-24  
**Статус:** APPROVED — implemented (verify migrate + manual paste/QR)  
**Источник:** [`docs/ideas/student-multi-photo-answer-paste.md`](../ideas/student-multi-photo-answer-paste.md)  
**Родитель:** [`SPEC.md`](../../SPEC.md) §1.9.8 (written homework photo), uploads  
**Связано:**  
- [`clipboard-image-intake.md`](clipboard-image-intake.md) — paste/DnD уже есть; **этот spec supersedes** StepView limit=1 (US-CI-4)  
- [`written-homework-photo-submit`](../ideas/written-homework-photo-submit.md) — ранее «несколько фото» было Not Doing; снимаем ограничение с лимитом 3  
- Teacher review / `ImageViewer` / `WrittenAnswerReview` / `HomeworkSubmissionPhotos`  
**План:** [`tasks/student-multi-photo-answer-paste.md`](../../tasks/student-multi-photo-answer-paste.md)

---

## Assumptions (проверьте до IMPLEMENT)

Если не поправите — считаем принятыми:

1. **Лимит 3** фото на `self_check` шаг (всего на шаг, не за одно paste-событие).
2. **Текст «Ваш ответ» не убираем** и не делаем обязательным для compare в ДЗ (как сейчас: достаточно ≥1 фото).
3. **Source of truth:** JSON-колонка `answer_image_ids: list[uuid]` на `test_session_steps`. Миграция: backfill из `answer_image_id`, затем **drop** `answer_image_id` (+ FK). FE и BE обновляются в одном релизе — singular fields в API **не** оставляем как permanent aliases.
4. **Attach = append.** `POST …/answer-image` с одним `answer_image_id` добавляет в конец, если `len < 3` и шаг не `checked`. При `len == 3` → **422**. Дубликат id → **422**.
5. **Remove до compare:** `DELETE …/answer-image/{image_id}` разрешён пока статус ≠ `checked`. После `checked` — **409** (как сейчас нельзя менять фото).
6. **Compare / submit ДЗ:** требуется `len(answer_image_ids) >= 1` для homework `self_check` (вместо «`answer_image_id` is not None»).
7. **Paste UX как у учителя:** зона intake оборачивает **поле ответа + галерею + кнопки**. Ctrl/Cmd+V с `image/*` при фокусе в инпуте → upload+append (`preventDefault`). Text-only clipboard → обычный paste в поле (без `preventDefault`).
8. **Multi paste/drop:** за одно событие загружаем файлы по порядку до заполнения слотов (остаток лимита); лишние — игнор + короткое сообщение.
9. **Handoff (QR):** пока `len < 3`, новое фото с телефона **append**, не replace. Когда `len == 3` — handoff create / capture отклоняет с понятной ошибкой (или UI не предлагает QR).
10. **Превью ученика:** читаемая галерея (как иллюстрации в тестах / `AuthenticatedImage`), не только текст «Фото прикреплено». Кнопка удалить на каждом превью до `checked`.
11. **Teacher review:** показывать **все** URL шага (листание или вертикальный список). Новый lightbox **не** обязателен; расширить `ImageViewer` / `WrittenAnswerReview` / `HomeworkSubmissionPhotos`.
12. **RBAC uploads:** `student_can_view` / `teacher_can_view_answer_image` учитывают id **в массиве** `answer_image_ids` (не только старое FK).
13. **Practice self_check** без homework: фото по-прежнему опциональны; если ученик прикрепляет — тот же лимит 3 и тот же intake.
14. **MIME** без изменений: jpeg/png/webp через существующий `uploadImage`.
15. **Desktop-first** для clipboard; мобильный file picker / QR без изменений по ценности.

→ Поправьте нумерованные пункты, иначе после approve идём в IMPLEMENT с ними.

---

## 1. Objective

### Что строим

Ученик на шаге самопроверки может прикрепить **до 3** фото/скринов ответа (paste из буфера с фокусом в «Ваш ответ», DnD, file picker, QR), видеть галерею и удалять фото до сравнения. Преподаватель видит все страницы при проверке ДЗ.

### Зачем

Ответ часто на 2+ тетрадных страницах; одно фото заставляет склеивать или обрезать. Hint про Ctrl+V вводит в заблуждение: paste зона не покрывает поле ответа.

### Для кого

| Роль | Эффект |
|------|--------|
| **Ученик** | Несколько страниц + paste «как в конструкторе» |
| **Преподаватель** | Видит полный рукописный ответ по страницам |

### User stories + acceptance

| ID | Story | Acceptance |
|----|--------|------------|
| US-MP-1 | Как ученик, вставляю скрин из буфера, когда курсор в «Ваш ответ» | Image paste → append в галерею; text paste в поле работает |
| US-MP-2 | Как ученик, добавляю до 3 фото (paste/DnD/file) | 4-е отклоняется с сообщением; до 3 — ок |
| US-MP-3 | Как ученик, удаляю одно фото до «Сравнить» | DELETE → галерея обновляется; compare при ≥1 в ДЗ |
| US-MP-4 | Как ученик, снимаю 2-ю страницу с телефона по QR | Handoff append, пока `<3` |
| US-MP-5 | Как ученик в ДЗ, сравниваю ответ | Compare без фото → 422; с ≥1 → ок; после checked галерея read-only |
| US-MP-6 | Как преподаватель, вижу все фото шага в review | Все `answer_image_urls` доступны в UI проверки |
| US-MP-7 | Как система, чужой ученик не читает чужие answer-фото | GET upload → 403 вне владельца/своего ДЗ/темы |

---

## 2. Tech Stack

| Слой | Стек |
|------|------|
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic v2 |
| Frontend | Next.js App Router, React client, Vitest + RTL |
| Upload | `POST /api/uploads/images` (без изменений контракта upload) |
| Intake | `frontend/lib/image-intake.ts` (лимит события = остаток слотов) |

Новых npm/pip зависимостей **не требуется**.

---

## 3. Commands

```bash
# Backend
cd backend
source .venv/bin/activate   # или .venv\Scripts\activate
alembic upgrade head
pytest tests/test_homework_written_photo.py tests/test_upload_handoff.py tests/test_uploads_api.py -q
pytest -q

# Frontend
cd frontend
npm run test -- --run components/tests/StepView.test.tsx
npm run test -- --run components/homework/
npm run lint
npm run build
```

---

## 4. Project Structure

```
backend/
  alembic/versions/0xx_step_answer_image_ids.py
  app/models/test_session.py          # answer_image_ids
  app/schemas/test_session.py         # StepRead / attach / delete responses
  app/schemas/homework.py             # submission step URLs list
  app/schemas/handoff.py
  app/services/test_session/*.py      # attach append, compare guard
  app/services/upload_handoff_service.py
  app/services/homework_*.py
  app/repositories/app/upload_repo.py # RBAC by array membership
  tests/…

frontend/
  components/tests/StepView.tsx       # intake wrapper + gallery
  components/homework/WrittenAnswerReview.tsx
  components/homework/HomeworkSubmissionPhotos.tsx
  components/homework/ImageViewer.tsx # optional: multi src / pager
  lib/api/tests.ts                    # attach + delete + types
  lib/api/types.ts
  lib/image-intake.ts                 # unchanged API; callers pass limit=remaining
```

Docs: этот spec + plan; обновить ссылку в clipboard-image-intake (StepView limit).

---

## 5. Code Style / API contract

### Persistence

```python
# test_session_steps
answer_image_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
# max length enforced in service (≤3), not DB CHECK required for MVP
```

### Read (step)

```json
{
  "position": 1,
  "answer": "…",
  "answer_image_ids": ["uuid-1", "uuid-2"],
  "answer_image_urls": [
    "/api/uploads/images/uuid-1",
    "/api/uploads/images/uuid-2"
  ]
}
```

Singular `answer_image_id` / `answer_image_url` **удаляются** из `StepRead` в том же релизе.

### Attach (append)

```http
POST /api/tests/sessions/{id}/steps/{n}/answer-image
{ "answer_image_id": "<uuid>" }
```

Response:

```json
{
  "position": 1,
  "answer_image_ids": ["…", "…"],
  "answer_image_urls": ["…", "…"]
}
```

### Delete

```http
DELETE /api/tests/sessions/{id}/steps/{n}/answer-image/{image_id}
```

→ 200 с тем же shape, что attach; 404 если id не в списке; 409 если checked.

### Handoff capture response

Те же `answer_image_ids` / `answer_image_urls` (полный список после append).

### Homework teacher detail

`submission_steps[].answer_image_urls: string[]` (замена singular).

---

## 6. Testing Strategy

| Уровень | Что |
|---------|-----|
| pytest | Migration backfill; append до 3; 4-й → 422; delete; compare/submit guards; handoff append; RBAC array |
| vitest | Paste с фокусом в input; multi-file truncate to remaining; gallery remove; disabled after checked |
| Manual | Chrome: Ctrl+V в поле ответа; QR 2-я страница; teacher видит 2–3 фото |

---

## 7. Boundaries

**Always**
- TDD на лимит и paste-from-input
- `credentials: 'include'` для upload/image GET
- Не ломать text paste

**Ask first**
- Менять лимит 3
- Оставлять deprecated singular API fields дольше одного релиза
- PDF / склейка страниц

**Never**
- Убирать текстовое поле ответа в рамках этой фичи
- Разрешать изменение галереи после `checked`
- CapturePage → rich paste editor

---

## 8. Success Criteria

- [x] Ученик с фокусом в «Ваш ответ» вставляет скрин → фото в галерее
- [x] Можно иметь 1..3 фото; 4-е отклонено
- [x] Можно удалить фото до compare
- [x] ДЗ compare/submit требуют ≥1 фото
- [x] QR добавляет страницу при `len < 3`
- [x] Teacher review показывает все фото шага
- [x] pytest + StepView/homework vitest зелёные
- [x] Старые сессии с одним фото после migrate читаются как массив длины 1

---

## 9. Open Questions

Нет блокирующих (решения зафиксированы в Assumptions). Неблокирующие:

1. Нужен ли явный UI «Страница 1/2/3» у учителя или достаточно вертикального списка?
2. Сообщение при переполнении: toast vs inline `role="alert"` (предпочтение: inline как текущие ошибки StepView)?

---

## 10. Out of scope

- Reorder страниц drag-and-drop  
- Склейка / PDF  
- Лимит ≠ 3  
- Пересъёмка после checked  
- Изменения конструктора учителя (кроме косвенного parity paste UX у ученика)
