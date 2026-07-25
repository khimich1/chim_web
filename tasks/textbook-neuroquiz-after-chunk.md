# Implementation Plan: Нейроквиз после чанка

**Источник:** [`docs/specs/textbook-neuroquiz-after-chunk.md`](../docs/specs/textbook-neuroquiz-after-chunk.md) v0.2.0  
**Идея:** [`docs/ideas/textbook-neuroquiz-after-chunk.md`](../docs/ideas/textbook-neuroquiz-after-chunk.md)  
**Дата плана:** 2026-07-25  
**Статус:** IMPLEMENT done (NQ-1…NQ-8)  
**Skills:** planning-and-task-breakdown → incremental-implementation → TDD  
**Коммиты:** только по явной просьбе пользователя

### Progress

| Task | Статус |
|------|--------|
| NQ-1 Flag + schema + enums | ✅ |
| NQ-2 Generate (mock) + warmup/GET | ✅ |
| NQ-3 Answer + points + scoring lock | ✅ |
| NQ-4 Skip + votes/dislike | ✅ |
| NQ-5 Overlay UI + client API | ✅ |
| NQ-6 ChunkViewer wire + навигация | ✅ |
| NQ-7 Real LLM generate | ✅ |
| NQ-8 Env example + docs polish | ✅ |

---

## Overview

Ученик в учебнике по «Далее» получает оверлей с до 4 MCQ по чанку. Гибрид `qa_*` + DeepSeek (дистракторы / добивка), кэш Postgres, warm-up при открытии чанка, +1 за верный (lock после полного прохождения), Skip/Escape остаются на тексте без lock, лайк/дизлайк ученика, флаг `NEUROQUIZ_ENABLED`.

---

## Architecture Decisions

| Решение | Выбор | Почему |
|---------|--------|--------|
| Namespace | `/api/neuroquiz` отдельный router | Не раздувать textbook; чёткий feature flag |
| LLM в срезах | Сначала **mock generator** (фикстуры JSON), потом NQ-7 real | Fail-fast на API/баллах без $ и flaky LLM |
| Warm-up | `POST .../warmup` вызывает ensure-cache; клиент fire-and-forget | Spec 7A; без 202/poll |
| Scoring lock | `neuroquiz_chunk_attempts.completed=true` только после последнего ответа прохода | Spec Assump. 3 |
| Skip | Клиент закрывает оверлей; `POST /skip` опционален (телеметрия) или no-op 204 | Не пишет completed |
| Points | `ActivityEventType.NEUROQUIZ_CORRECT`, +1, `ref_id=str(question.id)` | Как ledger Phase 13 |
| Flag off | Backend 404 на neuroquiz; frontend «Далее» = старое поведение | Spec 13B |
| Last chunk complete | `router.push` на каталог `/student/textbook` (или текущий «Все темы» href) | Spec Assump. 2 |
| Catalog URL | Тот же, что ссылка «Все темы» на странице темы | Один источник правды в UI |

**ДОПУЩЕНИЯ плана (из approved spec):** 1–14 без изменений.

→ Поправь сейчас, иначе после «ок / tasks implement» идём с этим.

---

## Dependency graph

```
NQ-1 flag + Alembic + models + enums + empty router gate
        │
        ▼
NQ-2 mock generate + repo + warmup/GET          ← риск кэша рано
        │
        ├── NQ-3 answer + activity + complete lock
        │         │
        │         └── NQ-4 skip + vote/dislike retire
        │                   │
        │                   └── Checkpoint A (backend API зелёный)
        │
        └── NQ-5 overlay + lib/api/neuroquiz (можно параллельно с NQ-3/4 по контракту)
                  │
                  └── NQ-6 ChunkViewer + nav rules + flag
                            │
                            └── Checkpoint B (E2E-ручной с mock LLM)
                                      │
                                      └── NQ-7 real LLM
                                      └── NQ-8 .env.example + cross-links
                                                │
                                                └── Checkpoint C (done)
```

**Минимум для демо ученику (с mock):** NQ-1…NQ-6.  
**Параллельно:** после NQ-2 контракт стабилен → NQ-5 (frontend) || NQ-3/4 (backend).

---

## Risks & mitigations

| Риск | Влияние | Митигация |
|------|---------|-----------|
| LLM галлюцинации / битый JSON | Плохие вопросы | Mock first; structured output + schema validate; F3 Retry/Skip |
| Warm-up не успевает | Спиннер на «Далее» | Ожидаемо; Retry; не блокировать чтение |
| Один дизлайк убивает пул | Мало вопросов | Догенерация при `<4` active; мониторинг later |
| Двойной «Далее» / race submit | Двойные баллы | Ledger unique + disable UI after click |
| Flag default | Случайно выкл/вкл на проде | Default `false` в Settings; явно включить в `.env` |
| Последний чанк: «Далее» сейчас disabled | Нет квиза | NQ-6: enable «Далее» когда flag on |

---

## Task List

### NQ-1: Feature flag + schema foundation

**Description:** `NEUROQUIZ_ENABLED` в Settings; Alembic: `neuroquiz_questions`, `neuroquiz_chunk_attempts`, `neuroquiz_votes`; enums (`NEUROQUIZ_CORRECT`, question status/source, vote value); router stub + gate (flag off → 404); register in `main.py`.

**Acceptance:**
- [ ] Migration upgrade/downgrade
- [ ] Flag false → neuroquiz routes 404
- [ ] Models importable; enum в activity

**Verify:** `alembic upgrade head`; `pytest` на gate 404; app starts

**Deps:** None  
**Files:** `config.py`, `.env.example`, `enums.py`, `models/neuroquiz.py`, `models/activity` wiring, `alembic/versions/…`, `routers/neuroquiz.py`, `main.py`  
**Scope:** Medium

---

### NQ-2: Mock generate + warmup/GET

**Description:** Service `ensure_questions(topic, chunk_idx)` читает lecture/qa из content DB; если active `<4` — **mock** генератор пишет MCQ в Postgres; `POST warmup`, `GET` session (без correct ids); `scoring_enabled` по completed attempt.

**Acceptance:**
- [ ] Warmup создаёт ≥1..4 active questions
- [ ] GET возвращает prompts+options без correct_option_id
- [ ] Повторный warmup идемпотентен (не плодит дубли без нужды)

**Verify:** `pytest tests/test_neuroquiz.py -q` (mock)

**Deps:** NQ-1  
**Files:** `neuroquiz_repo.py`, `neuroquiz_service.py`, `neuroquiz_generate.py` (mock), `schemas/neuroquiz.py`, router, tests  
**Scope:** Large

---

### NQ-3: Answer + points + scoring lock

**Description:** `POST .../answer`; проверка на сервере; +1 через `activity_service`; `ref_id=question.id`; после последнего вопроса прохода → `completed=true`; дальнейшие answers → `points_awarded=0`.

**Acceptance:**
- [ ] Верный → +1 один раз
- [ ] Повтор того же question_id → 0
- [ ] После complete все answers → 0, `scoring_enabled=false` на GET
- [ ] Неверный → correct_option_id + explanation, 0 баллов

**Verify:** pytest cases выше; stats endpoint отражает +1

**Deps:** NQ-2  
**Files:** service, activity_service hook, router, tests  
**Scope:** Medium

---

### NQ-4: Skip + votes

**Description:** Skip не пишет completed; `POST .../vote` like/dislike; dislike → `status=retired`; при GET/warmup догенерация если active `<4`.

**Acceptance:**
- [ ] Skip → completed остаётся false; позже можно +1
- [ ] Dislike ретирит для всех
- [ ] Like сохраняется; смена на dislike ретирит

**Verify:** pytest

**Deps:** NQ-3  
**Files:** service, repo, router, tests  
**Scope:** Medium

---

### Checkpoint A (после NQ-1…4)

- [x] `pytest tests/test_neuroquiz.py` зелёный
- [x] uvicorn стартует; OpenAPI `/api/neuroquiz` виден при flag on
- [x] Flag off → 404

---

### NQ-5: NeuroQuizOverlay + API client

**Description:** `lib/api/neuroquiz.ts` + `NeuroQuizOverlay`: loading/Retry/Skip, вопрос, клик-ответ, верно/неверно, лайк до Next, Escape=Skip; vitest на состояния.

**Acceptance:**
- [ ] US-NQ-1,2,4,5 в unit/RTL (mock fetch)
- [ ] Голос только post-answer pre-next
- [ ] Escape вызывает onSkip (остаться)

**Verify:** `npm run test -- NeuroQuiz`

**Deps:** NQ-2 (контракт; можно на MSW до NQ-4)  
**Files:** `NeuroQuizOverlay.tsx`, `.test.tsx`, `lib/api/neuroquiz.ts`, types  
**Scope:** Medium

---

### NQ-6: ChunkViewer integration

**Description:** Warmup on chunk load если flag on; «Далее» → overlay; complete → next chunk или каталог; Skip/Escape → stay; сайдбар/Назад без overlay; при flag off — старое «Далее»; последний чанк: «Далее» enabled если flag on.

**Acceptance:**
- [ ] US-NQ-6,7,8
- [ ] ChunkViewer tests обновлены
- [ ] Ссылка каталога = «Все темы»

**Verify:** `npm run test -- ChunkViewer NeuroQuiz`; ручной с flag on + mock

**Deps:** NQ-5, NQ-3 (complete), NQ-4 (skip)  
**Files:** `ChunkViewer.tsx`, tests, возможно page link helper  
**Scope:** Medium

---

### Checkpoint B

- [ ] Ручной поток с `NEUROQUIZ_ENABLED=true` / `NEXT_PUBLIC_NEUROQUIZ_ENABLED=true` и mock/LLM
- [x] Баллы в stats (pytest); Skip остаётся на тексте; last chunk → каталог после complete (vitest)

---

### NQ-7: Real LLM generator

**Description:** Заменить mock на DeepSeek/structured JSON по C1; validate 4 options; ошибки → failed + F3 на клиенте уже есть.

**Acceptance:**
- [ ] Генерация на реальном чанке (dev) даёт валидный MCQ
- [ ] Невалидный ответ LLM не пишет мусор в DB (rollback/retry)
- [ ] pytest с mock LLM adapter остаётся зелёным

**Verify:** ручной 1–2 чанка; pytest

**Deps:** NQ-2…6  
**Files:** `neuroquiz_generate.py`, LLM factory usage, tests with fake LLM  
**Scope:** Medium

---

### NQ-8: Docs / env polish

**Description:** `.env.example` `NEUROQUIZ_ENABLED`; ссылка из idea/spec; при необходимости одна строка в SPEC.md §1.1.

**Acceptance:**
- [ ] Flag задокументирован
- [ ] Spec status → IMPLEMENT in progress / done when finished

**Verify:** file review  
**Deps:** NQ-7 (или параллельно с NQ-7)  
**Scope:** Small

---

### Checkpoint C (done)

- [x] Success criteria spec §1 (pytest + vitest)
- [x] Flag off не меняет UX учебника (vitest)
- [x] Нет TestSession coupling
- [ ] Ручной E2E в браузере (осталось ops)

### TDD coverage audit (2026-07-25)

Behavioral gaps closed with regression tests (no product bugs found — all new assertions green):

| Behavior | Where covered |
|----------|----------------|
| Scoring lock + replay 0 pts | `test_full_pass_locks_scoring`, `test_correct_points_are_idempotent_in_student_stats` |
| Skip no lock | `test_skip_does_not_lock_scoring`, `test_skip_without_answers_keeps_scoring_enabled` |
| +1 idempotent (ledger/stats) | `test_correct_points_are_idempotent_in_student_stats` |
| Dislike retire + denylist regen | `test_dislike_retires…`, `test_like_then_dislike_retires…`, `test_warmup_retires_questions_with_generic_distractors` |
| Flag off (GET/warmup/answer/vote/skip) | `test_neuroquiz_*_flag_off_*` |
| Warmup | `test_warmup_*` + ChunkViewer warmup on load |
| Overlay only on Далее | ChunkViewer: sidebar/Назад do not open; Далее opens |
| Escape=skip stay | Overlay Escape→onSkip; ChunkViewer skip stays on chunk |
| Salute + reduced-motion | Overlay tests |
| Votes only after answer | Overlay: icons absent pre-answer; vote API after answer |
| Complete nav | last → catalog; non-last → next chunk |

**Verify:** `pytest tests/test_neuroquiz.py` → 19 passed; `npm run test -- NeuroQuiz ChunkViewer` → 20 passed.

---

## Verification commands

```bash
cd backend && alembic upgrade head && pytest tests/test_neuroquiz.py -q
cd frontend && npm run test -- NeuroQuiz ChunkViewer && npm run lint
```

Ручной: `NEUROQUIZ_ENABLED=true` → ученик → чанк → Далее → 4 вопроса → stats.

---

## Out of plan (как в spec)

Teacher UI, like thresholds, ProgressWidget neuro line, TestSession, 202/poll warm-up, lecture-hash invalidation.

---

## Next

1. Approve этот PLAN (правки номерами NQ-*).  
2. Скажи **«implement NQ-1»** или **«implement с NQ-1»** — код только после явного старта.  
3. Полный task file уже здесь; отдельный breakdown не дублируем, пока не попросишь.
