# Teacher feedback composer UX

**Проект:** `chim_web`  
**Дата:** 2026-07-25  
**Статус:** идея согласована → спека [`docs/specs/teacher-feedback-composer-ux.md`](../specs/teacher-feedback-composer-ux.md)

**Связано:**

- [`teacher-written-homework-review.md`](teacher-written-homework-review.md) — базовая проверка письменных ДЗ (§1.9.9)
- [`clipboard-image-intake.md`](clipboard-image-intake.md) — paste/DnD уже в `StepFeedbackForm`
- [`student-multi-photo-answer-paste.md`](student-multi-photo-answer-paste.md) — QR + устройство + галерея у ученика

---

## Problem Statement

How might we сделать форму разбора ДЗ у преподавателя простой: текст + голос + фото (в т.ч. с телефона), без трёх одинаковых секций и без сырого file picker?

## Recommended Direction

**Composer sheet + photo intake как у ученика (буфер / устройство / QR).**

- Крупный выделенный textarea-лист; на нём иконка **микрофона**.
- Кнопка **«Сохранить»** — скруглённая, жирнее, справа.
- Фото: Ctrl+V / DnD, «с устройства», **QR** — и в разборе шага, и в общем комментарии.
- QR ведёт на **ту же** `/student/capture/...` (без отдельного teacher-маршрута).
- С телефона фото **сначала только в форму**: превью, можно удалить / добавить ещё; ученику уходит только после «Сохранить».

## Key Assumptions to Validate

- [ ] Одна capture-страница нормально обслуживает и ответ ученика, и фото разбора учителя (разный handoff-тип внутри токена)
- [ ] Иконка mic на листе понятна без отдельной секции «Голосовой комментарий»
- [ ] Превью + удалить/добавить до Save совпадает с ожиданием при проверке 5–15 сдач за вечер

## MVP Scope

**In**

- Редизайн `StepFeedbackForm` / `VoiceRecorder`: лист, mic, «Сохранить» справа
- Intake UI: буфер, устройство, QR (и per-step, и общий комментарий)
- Handoff под feedback images → тот же `/student/capture/{token}`; upload кладёт файл в staging/slots формы, не публикует feedback
- Превью прикреплённых фото, удаление, добавление до лимита
- Vitest + смоук QR → превью → Save → ученик видит

**Out**

- `/teacher/capture/...`
- Автосохранение feedback при съёмке
- Очередь сдач / cockpit / merge двух блоков комментария

## Not Doing (and Why)

- Отдельная teacher capture page — лишняя сущность при той же съёмке
- Persist feedback до «Сохранить» — нельзя спокойно проверить/удалить фото
- Переиспользовать student handoff as-is без типа «feedback» — писал бы в ответ ученика

## Open Questions

- Нет блокирующих; детали handoff-типа и polling — в спеке.
