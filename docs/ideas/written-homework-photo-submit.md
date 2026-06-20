# Письменные задания: фото в ДЗ vs сравнение в практике

**Проект:** `chim_web`  
**Дата:** 2026-06-20  
**Статус:** идея согласована → формализация в [`SPEC.md`](../../SPEC.md) §1.9.8, план — Phase 14 Task 75 (+ доработка Task 72)

**Связано:** [`teacher-task-constructor.md`](teacher-task-constructor.md) — расширяет модель `self_check` из конструктора заданий.

---

## Problem Statement

**Как разделить письменные задания (`self_check`) на режим самообучения и режим сдачи ДЗ, чтобы в свободной практике ученик только сверялся с эталоном, а в домашке обязательно прикреплял фото рукописного решения для проверки преподавателем?**

---

## Recommended Direction

**Контекстный gating по `TestSession.homework_assignment_id`** — без нового `grading_mode` и без флагов на задании.

| Контекст | Вход | Фото рукописи | «Сравнить ответ» | Преподаватель |
|----------|------|---------------|------------------|---------------|
| **Практика** | Вкладка «Темы» в тестах (`homework_assignment_id = null`) | Нет | Сразу | Не видит ответ |
| **Сдача ДЗ** | ДЗ с пунктом `custom_theme` (`homework_assignment_id` задан) | **Обязательно** | После успешного upload | Видит фото в карточке сдачи |

### Согласованные UX-решения (2026-06-20)

| Тема | Решение |
|------|---------|
| Что такое «запись» | Фото рукописного решения (jpeg/png/webp), не аудио/видео |
| Текст в ДЗ | **Опционален**; для завершения шага достаточно фото |
| Порядок действий в ДЗ | Upload → кнопка «Сравнить ответ» активна (отдельной «Отправить» нет) |
| Замена фото | Разрешена **до** нажатия «Сравнить»; после `checked` — заблокировано |
| Кто включает фото | Автоматически: любое `self_check` в сессии с `homework_assignment_id` |

### Flow (ДЗ)

```
1. Ученик открывает self_check из ДЗ
2. Прикрепляет фото (обязательно) — POST /api/uploads/images
3. «Сравнить ответ» разблокируется
4. После сравнения — эталон на экране, шаг checked, фото заблокировано
5. При submit ДЗ преподаватель видит фото по каждому self_check шагу
```

### Flow (практика)

```
1. Ученик открывает тему во вкладке «Темы»
2. Опциональный текст + «Сравнить ответ» (без upload)
3. Эталон на экране; преподаватель не получает данные
```

---

## Key Assumptions to Validate

- [ ] Ученики снимают решение на телефон достаточно чётко (без OCR в MVP).
- [ ] `answer_image_id` на `TestSessionStep` + RBAC достаточен для teacher review без отдельной сущности «SubmissionAttachment».
- [ ] Блокировка «Сравнить» до upload снижает списывание (ученик не видит эталон до сдачи фото).
- [ ] Преподавателю достаточно **просмотра** фото без оценки/комментария в v1.

---

## MVP Scope

### IN

- `TestSessionStep.answer_image_id` (FK → upload)
- Backend: `compare` для `self_check` в ДЗ без `answer_image_id` → `422`
- Frontend `StepView`: upload только при `homework_assignment_id`; gating кнопки «Сравнить»
- Teacher UI: фото self_check шагов в деталях сдачи ДЗ (`GET /api/homework/{id}` для teacher)
- Submit ДЗ: все `self_check` шаги должны иметь `answer_image_id`

### OUT

- Оценка/комментарий преподавателя к фото
- AI-проверка рукописи, OCR
- Несколько фото на шаг
- Аудио/видео-записи
- Пересдача фото после `checked`
- Отдельный флаг `requires_photo` на задании (контекст ДЗ достаточен)

---

## Not Doing (and Why)

| Исключено | Причина |
|-----------|---------|
| Флаг на задании `requires_photo` | Дублирует правило «в ДЗ = сдача с фото» |
| Upload в свободной практике | Противоречит цели «только сравнить» |
| «Отправить» отдельно от «Сравнить» | Лишний шаг; upload уже сохраняет работу |
| Замена фото после сравнения | Ученик уже видел эталон |
| Teacher grading score за письменные | Вне scope; self_check не в `score` сессии |

---

## Data model (дополнение)

```
TestSessionStep (расширение)
  ├── answer_image_id? (uuid, FK uploads)   # обязателен для self_check в ДЗ
  └── answer? (text)                        # опционален в ДЗ; в практике — как сейчас
```

---

## Open Questions

_Все блокирующие вопросы закрыты на сессии idea-refine 2026-06-20._

---

## Codebase anchors

| Модуль | Изменение |
|--------|-----------|
| `TestSession.homework_assignment_id` | Различие практика / ДЗ |
| `custom_test_session_service.compare_step` | Валидация `answer_image_id` в ДЗ |
| `StepView.tsx` | Контекстный UI upload + gating |
| `homework_service` / teacher homework detail | Галерея фото по шагам |
| `POST /api/uploads/images` | Без изменений контракта |

---

## Handoff

| Следующий шаг | Артефакт |
|---------------|----------|
| ~~idea-refine~~ | ✅ этот документ |
| ~~spec-driven-development~~ | ✅ [`SPEC.md`](../../SPEC.md) §1.9.8, AC-7.9–7.10 |
| `planning-and-task-breakdown` | Task 72 (доработка) + Task 75 в [`tasks/plan.md`](../../tasks/plan.md) |
| `incremental-implementation` | После Tasks 66–69 (модель + compare API) |

---

## Ссылки

- [`teacher-task-constructor.md`](teacher-task-constructor.md) — базовый конструктор `self_check`
- [`SPEC.md`](../../SPEC.md) §1.9.8
- [`tasks/plan.md`](../../tasks/plan.md) — Tasks 72, 75
