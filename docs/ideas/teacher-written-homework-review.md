# Проверка письменных ДЗ преподавателем

**Проект:** `chim_web`  
**Дата:** 2026-06-20  
**Статус:** идея согласована → формализация в [`SPEC.md`](../../SPEC.md) §1.9.9, план — Phase 15

**Связано:**

- [`written-homework-photo-submit.md`](written-homework-photo-submit.md) — сдача фото учеником (§1.9.8, Task 75)
- [`teacher-task-constructor.md`](teacher-task-constructor.md) — `self_check`, `reference_answer`

---

## Problem Statement

**Как сделать удобную проверку письменных заданий в ДЗ, чтобы преподаватель видел фото рукописи с zoom/поворотом рядом с эталоном и мог отправить ученику голос и фото-разбор, при том что ученик фотографирует решение на телефоне, а решает и сдаёт ДЗ с компьютера?**

---

## Recommended Direction

**«Tutor workflow»** — три связанных потока без пересдачи и без статусов «принято/на доработку»:

| Роль | Поток |
|------|--------|
| **Ученик (ПК)** | ДЗ → шаг `self_check` → QR для телефона или upload с ПК → «Сравнить» → submit |
| **Ученик (телефон)** | Скан QR → камера с чеклистом и превью → одноразовая отправка фото на шаг |
| **Преподаватель** | Карточка сдачи → по каждому `self_check`: viewer + эталон + голос/фото/текст |
| **Ученик (после разбора)** | Бейдж «есть разбор» в списке ДЗ → голос/фото/текст при открытии сдачи |

### Согласованные UX-решения (2026-06-20)

| Тема | Решение |
|------|---------|
| Cross-device | QR на ПК → мобильная страница «только съёмка» для конкретного шага |
| Auth на телефоне | Гибрид: cookie → сразу камера; иначе логин или одноразовый token в QR (TTL ~15 мин) |
| Подсказки при съёмке | Чеклист + превью перед отправкой |
| Fallback на ПК | «Прикрепить с этого устройства» (как сейчас в `StepView`) |
| Экран преподавателя | Адаптивно: фото ученика и эталон **рядом** на десктопе, **столбиком** на узком экране |
| Viewer | Zoom, pan, поворот фото рукописи |
| Обратная связь | По каждому `self_check` шагу: голос + фото + текст (все опциональны, но хотя бы одно при «сохранить») |
| Общий комментарий | Опционально ко всей сдаче ДЗ (отдельно от per-step) |
| Статус проверки | Только факт **«есть разбор»** — без «принято» / «на доработку» |
| Пересдача фото | **Нет** — после `checked` фото заблокировано (как §1.9.8) |
| Голос (UX) | Без жёсткого лимита в интерфейсе |
| Голос (сервер) | Мягкий потолок ~10 мин + предупреждение в UI |
| Уведомление ученику | Бейдж «есть разбор» в списке ДЗ + детали при открытии |

### Flow: съёмка с телефона (QR)

```
1. Ученик на ПК открывает self_check в ДЗ
2. POST handoff-token → QR на экране
3. Телефон: /student/capture/{token} → чеклист → камера → превью → отправить
4. ПК: polling → «фото получено» → «Сравнить ответ» активна
5. После compare — эталон, шаг checked, фото заблокировано
```

### Flow: проверка преподавателем

```
1. Преподаватель открывает сданное ДЗ
2. Для каждого self_check: split-view (фото | reference_answer)
3. Записывает голос / прикрепляет фото / вводит текст → «Сохранить отзыв»
4. Опционально: общий комментарий к сдаче
5. Ученик видит бейдж в списке ДЗ и разбор при открытии
```

### Технический блокер (уже в prod UI)

`<img src="/api/uploads/...">` на teacher-странице не передаёт auth-cookies при разных origin (Next `:3000` ↔ API `:8000`). **Первый срез:** authenticated image proxy (blob fetch с `credentials` или Next route proxy).

---

## Key Assumptions to Validate

- [ ] QR → фото за &lt; 2 мин у реальных учеников (без лишнего логина).
- [ ] Split-view + zoom достаточен; преподавателю не нужна разметка на фото.
- [ ] Голосовой разбор слушают (не только текст/фото).
- [ ] `reference_answer` из конструктора покрывает эталон в 90% письменных заданий.
- [ ] Бейдж в списке ДЗ заменяет push/email в v1.

---

## MVP Scope

### IN — срез A (просмотр + QR)

- Authenticated image delivery для teacher/student UI
- `ImageViewer`: zoom, pan, rotate
- Teacher review UI: фото + `reference_answer` (адаптивный layout)
- `UploadHandoffToken` + mobile capture page + attach к шагу
- Polling на ПК после QR (без WebSocket)
- Чеклист + превью на мобильной странице съёмки

### IN — срез B (обратная связь)

- `TestSessionStepFeedback` (голос, фото[], текст, `published_at`)
- `HomeworkSubmissionFeedback` (опциональный общий комментарий)
- Запись голоса в браузере (`MediaRecorder` → webm/ogg), upload audio
- Teacher: сохранение отзыва по шагу + общий комментарий
- Student: бейдж `has_teacher_feedback` в списке ДЗ + UI разбора

### OUT

| Исключено | Причина |
|-----------|---------|
| Пересдача / rework | Сознательно убрано — лишнее усложнение |
| Статусы «принято» / «на доработку» | Достаточно «есть разбор» |
| OCR / AI-проверка рукописи | Roadmap v2; не в scope `self_check` |
| Рисование на фото ученика | Фото-ответ преподавателя покрывает кейс |
| WebSocket | Polling достаточен для QR-handoff |
| Несколько фото на шаг (ученик) | Усложняет viewer; одно фото как §1.9.8 |
| Push / email уведомления | Бейдж в списке ДЗ в v1 |
| Оценка баллами за письменный шаг | `self_check` вне `score` сессии |

---

## Data model (черновик)

```
UploadHandoffToken
  token, session_id, position, student_id, expires_at, used_at

TestSessionStepFeedback
  test_session_step_id (unique)
  teacher_text?
  teacher_voice_id?       # FK upload (audio)
  teacher_image_ids[]     # jsonb uuid[]
  published_at

HomeworkSubmissionFeedback
  homework_submission_id (unique)
  teacher_text?
  teacher_voice_id?
  teacher_image_ids[]?
  published_at
```

**Флаг для списка ДЗ:** `has_teacher_feedback` на submission — `true`, если есть хотя бы один `TestSessionStepFeedback` или `HomeworkSubmissionFeedback`.

---

## API (черновик)

| Метод | Путь | Роль |
|-------|------|------|
| POST | `/api/tests/sessions/{id}/steps/{pos}/handoff` | student |
| GET/POST | `/api/capture/{token}` | student (mobile) |
| GET | `/api/homework/{id}/review` | teacher — шаги + reference + feedback |
| PUT | `/api/homework/{id}/steps/{pos}/feedback` | teacher |
| PUT | `/api/homework/{id}/submission-feedback` | teacher (общий) |
| GET | `/api/student/homework/{id}/feedback` | student |

---

## Open Questions

_Блокирующих нет — готово к spec._

- Точный текст бейджа в списке ДЗ («Есть разбор» / «Разбор от преподавателя») — копирайт в spec.
- Формат audio upload (webm vs ogg) — по паттерну textbook audio в реализации.

---

## Codebase anchors

| Модуль | Изменение |
|--------|-----------|
| `HomeworkSubmissionPhotos.tsx` | Заменить на `WrittenAnswerReview` + viewer |
| `teacher/homework/[id]/page.tsx` | Review layout, feedback forms |
| `StepView.tsx` | QR-блок + handoff polling |
| `student/capture/[token]/page.tsx` | Новая мобильная страница |
| `homework_service` | `reference_answer`, feedback, `has_teacher_feedback` |
| `upload_service` | Audio upload type; handoff token RBAC |
| `GET /api/uploads/images/{id}` | Или Next proxy — cookie auth для `<img>` |

---

## Handoff

| Следующий шаг | Артефакт |
|---------------|----------|
| ~~idea-refine~~ | ✅ этот документ |
| ~~spec-driven-development~~ | ✅ [`SPEC.md`](../../SPEC.md) §1.9.9, AC-3.9, AC-7.11–7.16 |
| `planning-and-task-breakdown` | Phase 15 в [`tasks/plan.md`](../../tasks/plan.md) (Tasks 76–84) |
| `incremental-implementation` | Срез A → B после Phase 14 (Task 75) |

---

## Ссылки

- [`written-homework-photo-submit.md`](written-homework-photo-submit.md) — §1.9.8
- [`SPEC.md`](../../SPEC.md) §1.9.8
- [`tasks/plan.md`](../../tasks/plan.md) — Task 75 (фото в ДЗ)
