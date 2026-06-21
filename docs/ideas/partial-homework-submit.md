# Частичная сдача домашнего задания

**Статус:** согласовано (2026-06-21)  
**Связано:** SPEC §1.7, §1.8, §1.9.8 · `homework_submit_service` · Phase 6 / Task 100

## Проблема

Раньше сдача ДЗ требовала:

- фото на **всех** `self_check` шагах (включая неотвеченные);
- 100% выполнения тест-сессии;
- повторная сдача возвращала 409.

Ученик не мог сдать частичный прогресс и досдать позже.

## Решения (Approach A)

| Аспект | Решение |
|--------|---------|
| Когда можно сдать | После `TestSession.status = completed` (сессия завершена, но не все шаги обязаны быть отвечены) |
| Минимум | ≥1 шаг со статусом `checked` |
| Фото `self_check` | Только на **отвеченных** (`checked`) шагах |
| Прогресс | `answered_steps / total_steps` (шаги тест-сессии), напр. 3/5 = 60% |
| Статус ДЗ | `submitted` даже при частичной сдаче; `can_reopen=true` если `< 100%` |
| Баллы | Пропорционально: `round(50 × answered/total)`; дельта при досдаче через `homework_complete_delta` |
| Уведомление | Всегда при submit; payload: `answered_steps`, `total_steps`, `completion_percent` |
| Досдача | `POST /api/homework/{id}/reopen` → `in_progress` + та же сессия `in_progress`; locked шаги остаются locked (§1.9.8) |
| Resubmit | UPDATE той же `HomeworkSubmission`; повторное уведомление с новым % |
| UI | Кнопка «Досдать» без confirmation dialog |

## Потоки

### Частичная сдача

```
Ученик → завершает сессию (1+ checked) → POST submit
  → HomeworkSubmission (answered/total/%)
  → status=submitted, notify teacher
  → +пропорциональные баллы (homework_complete)
```

### Досдача

```
Ученик → POST reopen (только if completion < 100%)
  → assignment=in_progress, session=in_progress
  → дозаполняет шаги → complete session → POST submit
  → UPDATE submission, notify teacher, +delta баллы
```

## Модель данных

`homework_submissions`:

- `answered_steps`, `total_steps`, `completion_percent` (migration `017`)

`HomeworkRead.can_reopen` — вычисляемое поле (не в БД).

## Вне scope

- Пересдача фото после `compare` (по-прежнему locked, §1.9.8)
- Статусы «на доработку» / teacher reject partial submit
