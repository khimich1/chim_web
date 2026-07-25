# Spec: Нейроквиз после чанка учебника

**Версия:** 0.2.0  
**Дата:** 2026-07-25  
**Статус:** IMPLEMENT done (NQ-1…NQ-8) · PLAN: [`tasks/textbook-neuroquiz-after-chunk.md`](../../tasks/textbook-neuroquiz-after-chunk.md)  
**Feature flag:** `NEUROQUIZ_ENABLED` (backend, default false) + `NEXT_PUBLIC_NEUROQUIZ_ENABLED` (frontend overlay; default unset/false)  
**Источник:** [`docs/ideas/textbook-neuroquiz-after-chunk.md`](../ideas/textbook-neuroquiz-after-chunk.md)  
**Родитель:** [`SPEC.md`](../../SPEC.md) §1.1 (учебник), §1.8 (баллы)  
**Связано:** LLM-стек [`llm-provider.md`](llm-provider.md); activity ledger Phase 13  
**Не связано:** `TestSession` / раздел «Тесты»

---

## Assumptions (проверьте до PLAN)

Если не поправите — считаем принятыми:

1. **Триггер оверлея** — только кнопка **«Далее»** в нижней навигации чанка. Клик по чанку в сайдбаре (`ChunkNav`) и **«Назад»** оверлей **не** открывают.
2. **Навигация после оверлея (утверждено):**
   - **Прошёл квиз до конца** (ответил на все вопросы в проходе) на **последнем** чанке темы → уход в **каталог тем** (`/student/textbook` или список тем секции — тот же UX, что «Все темы»).
   - **Прошёл квиз до конца** на **непоследнем** чанке → переход к **следующему** чанку.
   - **Пропуск квиза** (кнопка «Пропустить» или Escape) → оверлей закрывается, ученик **остаётся на тексте текущего чанка** (никуда не переходим).
3. **Когда баллы больше не даются (утверждено):** scoring lock только после того, как ученик **полностью прошёл квиз** по чанку (ответил на все вопросы прохода). **Skip / Escape не закрывают** возможность баллов: позже снова «Далее» → можно отвечать и получать +1 за ещё не засчитанные верные вопросы. Повторный полный проход после lock → 0 баллов. Доп. защита: ledger идемпотентен по `question_id`.
4. **Уход mid-quiz** (закрыл вкладку / ушёл через сайдбар без Skip): lock **не** ставится; при следующем «Далее» квиз снова; баллы за вопросы, по которым ещё не было `NEUROQUIZ_CORRECT`.
5. **MCQ формат:** ровно **4 варианта** (1 верный + 3 дистрактора); у каждого варианта стабильный `option_id` в JSON кэша.
6. **После неверного ответа:** сразу показать верный вариант + короткий explanation; лайк/дизлайк доступны до «Далее»; повторный клик по варианту в том же проходе запрещён.
7. **Warm-up (утверждено = A):** при открытии чанка клиент вызывает `POST .../warmup` (не блокирует UI). Если к «Далее» кэша нет — оверлей: loading + Retry + Skip. Без 202/poll в MVP.
8. **API:** `/api/neuroquiz/...`, только student. Textbook API полями квиза не расширяем.
9. **Хранение:** кэш/попытки/голоса в **PostgreSQL**; `lecture`/`qa_*` читаем из SQLite только при генерации.
10. **Баллы:** `NEUROQUIZ_CORRECT` = **+1**, `ref_id` = UUID вопроса.
11. **Лайки MVP:** только ученик; дизлайк → вопрос retired для всех.
12. **Пул:** до 4 active-вопросов на чанк; после retire — догенерация при необходимости.
13. **Feature flag (утверждено = B):** `NEUROQUIZ_ENABLED` в settings/env. Если `false` — API нейроквиза отвечает 404/403 с понятным телом; UI не открывает оверлей (кнопка «Далее» ведёт себя как сейчас: сразу следующий чанк / на последнем — без квиза). В `.env.example` описать флаг.
14. **Escape (утверждено):** как **Пропустить квиз** — закрыть оверлей, **остаться на тексте**, scoring lock **не** ставить.

→ Assumptions **1–14 утверждены**. Следующий шаг: PLAN.

---

## 1. Objective

### Что строим

Мини-нейроквиз в учебнике ученика: при «Далее» — фирменный полупрозрачный оверлей с до 4 MCQ по тексту чанка; опциональные баллы; лайки на вопросы; кэш в Postgres; генерация через DeepSeek (гибрид `qa_*` + текст).

### Зачем

Чтение чанка без самопроверки слабо закрепляет материал. Отдельные «Тесты» — другой режим. Нужна лёгкая проверка «по ходу учебника» с мягкой мотивацией (+1).

### Для кого

| Роль | Эффект |
|------|--------|
| **Ученик** | После чанка проверяет понимание; может пропустить; +баллы за верные (1 раз за чанк-попытку) |
| **Учитель** | Видит рост `total_points` у учеников; **без** UI квиза в MVP |
| **Система** | Кэш + лайки улучшают пул вопросов без ручной модерации |

### User stories + acceptance

| ID | Story | Acceptance |
|----|--------|------------|
| US-NQ-1 | Как ученик, после «Далее» вижу оверлей с вопросом и вариантами | Оверлей поверх текста чанка; 4 варианта; фирменный стиль |
| US-NQ-2 | Как ученик, могу пропустить квиз | «Пропустить» / Escape закрывают оверлей; **остаюсь на тексте чанка**; баллы позже ещё доступны |
| US-NQ-3 | Как ученик, за верный ответ получаю +1 | Ledger +1; тот же вопрос повторно → 0; после полного прохождения чанка все ответы → 0 |
| US-NQ-4 | Как ученик, вижу сразу результат ответа | Верно/неверно; при неверно — показан правильный; одна попытка на вопрос в проходе |
| US-NQ-5 | Как ученик, могу лайкнуть/дизлайкнуть после ответа до «Далее» | UI голоса; дизлайк ретирит вопрос для всех |
| US-NQ-6 | Как ученик, после полного прохождения снова вижу квиз без баллов | Оверлей есть; `scoring_enabled=false` / `points_awarded=0` |
| US-NQ-7 | Как ученик, не жду генерацию при обычном чтении | Warm-up при открытии чанка; если не готов — loading + Retry/Skip |
| US-NQ-8 | Как ученик на последнем чанке, тоже прохожу квиз по «Далее» | «Далее» не disabled только из-за конца списка |

### Success criteria (тестируемые)

- [ ] pytest: generate/cache, submit correct → +1 once, submit again → 0, skip does **not** lock scoring, full complete locks, dislike retires question
- [ ] vitest: оверлей open/close, answer lock, like only after answer, Skip
- [ ] Ручной: chunk → wait → Далее → 4 MCQ → баллы в `/api/students/me/stats`
- [ ] Нет связи с `TestSession`; teacher neuroquiz UI отсутствует
- [ ] `ruff` / `npm run lint` без новых ошибок в затронутых файлах

---

## 2. Tech Stack

| Слой | Стек |
|------|------|
| Backend | FastAPI, SQLAlchemy 2 async, Alembic, Pydantic v2 |
| Content | SQLite `prepared_lectures` (read-only на генерации) |
| App DB | PostgreSQL — кэш вопросов, попытки, голоса |
| LLM | Существующий provider (`LLM_*` / DeepSeek), structured JSON out |
| Frontend | Next.js App Router, client components в `ChunkViewer` |
| Баллы | `activity_service.record_event` |
| Тесты | pytest (API/service), Vitest + RTL (оверлей) |

---

## 3. Commands

```bash
# Backend
cd backend
source .venv/bin/activate  # или .venv\Scripts\activate
alembic upgrade head
pytest tests/test_neuroquiz.py -q
ruff check app/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run test -- NeuroQuiz
npm run lint
npm run dev
```

**Ручной чеклист**

1. Войти как ученик → учебник → тема с несколькими чанками.  
2. Открыть чанк, подождать ~30 с, «Далее» → оверлей.  
3. Верный ответ → проверить stats (+1). Тот же вопрос снова / повтор чанка → 0.  
4. Неверный → показан верный; лайк/дизлайк; «Далее».  
5. Skip / Escape → остаёмся на тексте; снова «Далее» → квиз, баллы ещё можно получить.  
6. Полный проход на последнем чанке → каталог тем; на непоследнем → следующий чанк.  
7. После полного прохода повторный квиз без баллов.  
8. Сайдбар / «Назад» — без оверлея.

---

## 4. Project Structure

```
backend/
  alembic/versions/0xx_neuroquiz.py
  app/models/neuroquiz.py          # Question, ChunkAttempt, Vote
  app/models/enums.py              # + NEUROQUIZ_CORRECT; question status
  app/schemas/neuroquiz.py
  app/repositories/app/neuroquiz_repo.py
  app/services/neuroquiz_service.py
  app/services/neuroquiz_generate.py  # LLM hybrid C1
  app/api/routers/neuroquiz.py
  tests/test_neuroquiz.py

frontend/
  components/textbook/NeuroQuizOverlay.tsx
  components/textbook/NeuroQuizOverlay.test.tsx
  components/textbook/ChunkViewer.tsx    # wire: warmup, Далее → overlay
  lib/api/neuroquiz.ts
  lib/api/types.ts                       # NeuroQuiz* types
```

Docs: этот файл; idea уже в `docs/ideas/textbook-neuroquiz-after-chunk.md`.  
План задач (после approve spec): `tasks/textbook-neuroquiz-after-chunk.md`.

---

## 5. Code Style

Следовать существующим router → service → repository; student deps как в textbook/activity.

```python
# Пример контракта ответа на submit (иллюстрация стиля)
class NeuroQuizSubmitResult(BaseModel):
    correct: bool
    correct_option_id: str
    explanation: str | None = None
    points_awarded: int  # 0 or 1
    quiz_completed: bool  # true after answering the last question → scoring lock
```

```tsx
// Оверлей: ответ только кликом по варианту; голос — после answer, до next
<button type="button" disabled={answered} onClick={() => submit(option.id)}>
  {option.text}
</button>
```

---

## 6. Testing Strategy

| Уровень | Что | Где |
|---------|-----|-----|
| Unit/service | C1 assemble (qa + pad), retire on dislike, scoring lock | `tests/test_neuroquiz.py` |
| API | auth 401/403, warmup, get quiz, submit idempotent, vote | тот же файл / TestClient |
| Frontend | overlay states: closed → loading → question → answered → next/skip | `NeuroQuizOverlay.test.tsx` |
| Manual | G3 timing, last chunk, visual brand overlay | чеклист §3 |

Coverage: критичные ветки баллов и retire — обязательно; LLM — mock.

---

## 7. Boundaries

**Always**

- Валидация ответа на сервере (клиенту не доверяем `correct`)
- Идемпотентность баллов через ledger `(student_id, event_type, ref_id)`
- Тесты на scoring lock и dislike-retire
- Не писать секреты LLM в логи/ответы API

**Ask first**

- Новые pip/npm зависимости
- Изменение формулы баллов (+1) или порогов лайков
- Инвалидация кэша при смене текста лекции
- Teacher UI квиза
- Смена правил scoring lock / навигации после Skip
- Default `NEUROQUIZ_ENABLED` (true vs false) при деплое

**Never**

- Связывать нейроквиз с `TestSession` / exam grading
- Показывать teacher neuroquiz UI в этом MVP
- Live-генерация полного квиза на каждый submit без кэша
- Начислять баллы за неверный ответ или за Skip
- Коммитить `.env` / API keys

---

## 8. Data model (app DB)

### `neuroquiz_questions`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | `ref_id` для баллов |
| topic | str | |
| chunk_idx | int | |
| position | int \| null | 0..3 в «базовом» наборе; null если ad-hoc replacement |
| prompt | text | текст вопроса |
| options_json | JSON | `[{id, text}, ...]` ровно 4 |
| correct_option_id | str | |
| explanation | text \| null | |
| source | enum | `qa_pair` \| `lecture_gen` |
| status | enum | `active` \| `retired` |
| created_at | timestamptz | |

Unique/index: `(topic, chunk_idx, status)` для выборки active.

### `neuroquiz_chunk_attempts`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| student_id | FK users | |
| topic | str | |
| chunk_idx | int | |
| completed | bool | true только после ответа на **все** вопросы прохода |
| completed_at | timestamptz \| null | |
| created_at | timestamptz | |

Scoring lock: если есть `completed=true` для `(student, topic, chunk_idx)` → новые submit дают 0 points (квиз всё равно выдаётся). **Skip не пишет** completed.

### `neuroquiz_votes`

| Column | Type | Notes |
|--------|------|-------|
| student_id | FK | |
| question_id | FK | |
| value | enum | `like` \| `dislike` |
| created_at | timestamptz | |

PK `(student_id, question_id)`. Dislike → `question.status = retired`.

---

## 9. API contract

Базовый prefix: `/api/neuroquiz`. Auth: student session cookie.

| Method | Path | Body / query | Response |
|--------|------|--------------|----------|
| POST | `/topics/{topic}/chunks/{idx}/warmup` | — | `204` или `{status: ready\|pending\|failed}` |
| GET | `/topics/{topic}/chunks/{idx}` | — | `NeuroQuizSession` (до 4 вопросов **без** `correct_option_id`) |
| POST | `/topics/{topic}/chunks/{idx}/answer` | `{question_id, option_id}` | `NeuroQuizSubmitResult` |
| POST | `/topics/{topic}/chunks/{idx}/skip` | — | `204` (только телеметрия/опционально; **не** scoring lock) |
| POST | `/questions/{question_id}/vote` | `{value: like\|dislike}` | `204` / `{status}` |

`NeuroQuizSession`:

```json
{
  "topic": "Кислоты",
  "chunk_idx": 0,
  "scoring_enabled": true,
  "questions": [
    {
      "id": "uuid",
      "prompt": "...",
      "options": [{"id": "a", "text": "..."}, ...]
    }
  ]
}
```

`scoring_enabled=false`, если ученик уже **полностью прошёл** квиз по чанку (`completed=true`).

Ошибки: `404` нет чанка; `409` ответ после уже answered в open pass (опционально); `503`/`422` генерация failed → клиент F3; `401`/`403` не student.

Генерация (внутренний service, не публичный detail):

1. Загрузить `lecture` + `qa_*` из content DB.  
2. Взять до 4 qa-пар → LLM дистракторы.  
3. Если `<4` → LLM доп. вопросы только из `lecture`.  
4. Upsert `neuroquiz_questions` status=active.  
5. Не затирать active liked-вопросы без нужды; retired не реанимировать автоматически в MVP.

---

## 10. UI spec

### Оверлей

- Полупрозрачный scrim + карточка в chem-стиле (teal accents, как учебник).
- Контент: номер «Вопрос k из n», prompt, 4 кнопки-варианта.
- После ответа: состояние верно (green) / неверно (red) + explanation; кнопки вариантов disabled.
- Ряд голосов 👍/👎 (или текстовые «Полезно» / «Плохой вопрос») — только post-answer, pre-next.
- Низ: **«Далее»** (след. вопрос или закрытие после последнего) **слева**; **«Пропустить квиз»** ниже/отдельно.
- Loading: спиннер + Retry + Skip.
- Не блокировать чтение до нажатия «Далее» (оверлея нет).

### Интеграция `ChunkViewer`

- `useEffect` on `(topic, chunkIdx)` → `warmup()`.
- «Далее» → open overlay.
- После **полного** прохождения: next chunk, или на последнем — **каталог тем**.
- **Skip / Escape** → закрыть оверлей, **остаться** на текущем чанке.
- Не открывать квиз из `ChunkNav` / «Назад».

---

## 11. Out of scope (MVP)

- Teacher preview / teacher votes  
- Пороги N likes vs 1 dislike  
- Отдельный ProgressWidget «нейроквиз»  
- Связь с тестами / homework  
- Offline batch CI генерации всех чанков (G3 on-demand достаточно)  
- Явная кнопка «Перезапустить» внутри оверлея (повтор = снова «Далее» позже)  
- Инвалидация кэша по hash(lecture) — later  

---

## Open Questions

Нет блокирующих. Мелочи (точный URL каталога тем после последнего чанка, копирайт кнопок лайка) — в PLAN/UI-срезе.

---

## Next

PLAN: [`tasks/textbook-neuroquiz-after-chunk.md`](../../tasks/textbook-neuroquiz-after-chunk.md). После approve плана — IMPLEMENT по NQ-1…NQ-8.
