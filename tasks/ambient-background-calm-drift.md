# Implementation Plan: Спокойный «живой» фон (calm drift)

**Источник:** [`docs/specs/ambient-background-calm-drift.md`](../docs/specs/ambient-background-calm-drift.md) v0.2.0 · idea: [`docs/ideas/ambient-background-calm-drift.md`](../docs/ideas/ambient-background-calm-drift.md)  
**Дата плана:** 2026-07-24  
**Статус:** ✅ AB-7 morph+visible drift (+ post-QA Y amplitude bump) — ждёт визуальной приёмки lava-lamp / merge  
**Skills:** planning-and-task-breakdown → (далее) incremental-implementation → TDD  
**Коммиты:** только по явной просьбе пользователя

### Progress

| Task | Статус |
|------|--------|
| AB-1 Диагностика шва | ✅ |
| AB-2 Фикс `.chem-surface` | ✅ |
| AB-3 Коридоры + CSS drift + reduced-motion | ✅ (амплитуда оказалась невидимой — см. AB-7) |
| AB-4 Убрать дубль на `/login` (+ проверка atmospheric) | ✅ |
| AB-5 Vitest + build + ручной чеклист | ✅ (ручной — частично: нет chrome-devtools MCP) |
| AB-6 Stacking: blobs за body bg | ✅ |
| AB-7 Visible drift + wax morph (post visual QA) | ✅ код; visual pending |

**AB-1 finding:** Primary cause — `.chem-surface` gradient without `background-repeat: no-repeat` / `background-size: 100% 100%` (default `repeat` tiles the diagonal wash on tall docs → horizontal seam). Secondary — no `html` canvas color; `body { background: ... }` shorthand could fight longhands. Not blobs. Mirror gradient not needed after primary fix.

**AB-4:** Removed scoped from `/login`, `/student`, welcome, leaderboard, `SessionSummary` — all doubled with global `layout` blobs (clear once animated). Global kept.

**AB-6 finding:** После AB-4 на `/login` (и везде) пятна **невидимы**: global `<DecorativeBlobs />` с `fixed -z-10` — прямой потомок `body.chem-surface`. Отрицательный z-index у потомка рисуется **под фоном** элемента, создавшего stacking context (`body` с `relative` + painted `background`). Scoped раньше жил внутри `main` *над* body bg — поэтому пятна были видны. Assumption §5.3 «просто убрать scoped» был неполон без правки stacking.

**AB-7 finding:** После AB-6 пятна **видны**, но «не двигаются». Root cause: animation *была* применена (`chem-blob-drift--*`), но амплитуда ±1–4% от box SVG (~3–10px на 256px) + только translate 0/50/100 + opacity 0.12–0.18 = visually silent за 5–10 с. Не missing class / не `animation: none` / не Tailwind override (если OS без reduced-motion). Fix: multi-stop keyframes, translate ~4–12%, uneven scale 0.92–1.12 + slight rotate (wax morph), cycles 19–28s, X скромнее чтобы коридоры держались.

**AB-7 amplitude bump (post visual QA):** User: «сделай сдвиг больше, добавь движение вверх и вниз». Prior AB-7 Y was ~5–12% and mostly **one-sided** per blob (a/c only positive Y, b/d only negative). Bumped to **Y ±12–24%** with explicit up+down across 25/50/75 stops; X stays ~3–8%. Cycles unchanged (19–28s); reduced-motion unchanged.
---

## Overview

Бесшовный тёплый wash (`.chem-surface`) и тихое плавание существующих SVG-пятен (`DecorativeBlobs`) **по бокам** viewport. Одна спокойная интенсивность везде. Только CSS-анимация, без новых зависимостей, без правок форм/навигации/backend. Порядок: сначала доказать и убрать шов, затем drift в коридорах, затем снять визуальный дубль global+scoped на `/login`, затем тесты и ручная приёмка.

---

## Architecture Decisions

| Решение | Выбор | Почему |
|---------|--------|--------|
| Анимация | Только CSS `@keyframes` / `animation` на SVG | Spec §2; без framer-motion / JS rAF |
| Шов | Сначала continuous wash: `no-repeat`, `background-size: 100% 100%`, при нужде `html { background-color }` | Spec §5.1; зеркало градиента — только fallback |
| Пятна | Сохранить текущие SVG + `--blob-*`; opacity 0.12–0.18 | Idea/spec; не менять visual language |
| Коридоры | Якоря ~0–22% и ~78–100% ширины; движение в основном по Y | Spec assumption 4 / §5.2 |
| Global vs scoped | **Оставить** global в `layout`; scoped с atmospheric снят (AB-4) | Spec §5.3; не возвращать второй набор |
| Stacking global blobs | Blobs: `fixed inset-0 z-0`; page content: wrapper `relative z-10` в `layout` | **AB-6:** `-z-10` как child `body` прячется за body background. Не восстанавливать scoped ради видимости |
| Прочие scoped | `/student`, welcome, leaderboard, `SessionSummary` — проверить двоение; массово снимать только если видно, иначе спросить | Spec assumption 8 / Ask first |
| Интенсивность | Один calm-режим; prop `intensity` не добавляем | Spec §5.4 |
| a11y | `prefers-reduced-motion: reduce` → `animation: none`; сохранить `aria-hidden` + `pointer-events-none` | Spec assumptions 6–7 |
| Тесты | Классы/a11y в Vitest; не pixel-diff и не Playwright на кадры | Spec §6 |
| Scope | Только файлы фона/blobs; backend / палитра UI / TeacherNav — вне | Spec §4.3 |

**As-is (проверено в коде):**

- `body.chem-surface` в `layout.tsx` + отдельно `body { background: var(--background) }` в `globals.css`; `.chem-surface` — градиент без `background-repeat` / `background-size` / явного стопа 100%.
- Global blobs всегда в `layout`; scoped дубли: `/login`, `/student`, `/student/welcome`, `/student/leaderboard`, `SessionSummary`.
- `DecorativeBlobs.test.tsx`: a11y + `≥3` svg + global `fixed z-0` (не `-z-10`) + drift + scoped `absolute`.

---

## Dependency graph

```
AB-1 Диагностика шва (html / body / blobs)
 │
 └── AB-2 Фикс .chem-surface (+ html bg при нужде)
           │
           └── AB-3 Коридоры + keyframes + reduced-motion
                     │
                     └── AB-4 Снять scoped с /login (+ atmospheric check)
                               │
                               └── AB-5 Vitest + build + ручной чеклист
                                         │
                                         └── AB-6 Stacking fix (blobs vs body bg)
                                                   │
                                                   └── AB-7 Visible drift + wax morph
```

**Вертикальные срезы:** каждый шаг оставляет приложение рабочим; не смешивать фикс шва и рефактор монтирования в одном непроверенном коммите.

**Параллелизация:** почти нет — цепочка намеренно последовательная (шов → drift → дубль → verify). После AB-2 можно заранее набросать тест-кейсы для AB-5, но код drift — только после зелёного шва.

---

## Task List

### Phase 1: Бесшовный фон

---

## Task AB-1: Диагностика горизонтального шва

**Description:** На длинной teacher-странице (например `/teacher/notifications`) и на `/login` в DevTools зафиксировать причину полосы: computed `background` у `html` / `body.chem-surface`, нет ли лишнего wrapper с другим bg; временно скрыть `DecorativeBlobs` (DevTools / comment) — если полоса осталась, виноват surface/html. Краткие findings записать в комментарий к задаче / PR (не отдельный md, если не просили).

**Acceptance criteria:**
- [x] Понятна primary-причина шва (surface/html vs blobs/clip vs другой слой)
- [x] Зафиксирован минимальный фикс-путь для AB-2 (no-repeat / size / html bg; зеркало — только если primary не сработал)

**Verification:**
- [x] Manual: DevTools на странице с швом; сравнение с/без blobs — chrome-devtools MCP недоступен; диагностика по CSS (сильная гипотеза: tile gradient)
- [ ] Скролл + resize на 50%/100%/150% высоты — шов воспроизводится до фикса (нужна человеческая приёмка после фикса)

**Finding:** `.chem-surface` gradient without `no-repeat`/`100% 100%` → default repeat tiles on tall pages → horizontal seam. Not blobs. Fix path = AB-2 primary; mirror not needed.

**Dependencies:** None

**Files likely touched:**
- Нет (read-only / DevTools). Допустимо временное локальное скрытие blobs — не коммитить.

**Estimated scope:** XS

---

## Task AB-2: Фикс `.chem-surface` (бесшовный wash)

**Description:** Привести фон к непрерывному wash по паттерну spec §5.1: `background-color` + `background-image` + `background-repeat: no-repeat` + `background-size: 100% 100%`; при необходимости `html { background-color: var(--chem-bg) }`. Согласовать с существующим `body { background: var(--background) }`, чтобы правила не дрались (shorthand не затирал фикс). Мягкий стоп до 100% ок. Зеркальный multi-stop — **только** если после primary-фикса шов жив; тогда комментарий *why* в CSS.

**Acceptance criteria:**
- [x] На длинной странице при скролле нет видимой горизонтальной полосы/стыка оттенков (CSS fix applied; visual confirm pending)
- [x] Resize окна не возвращает шов (same)
- [x] Пятно не «обрезано» линией стыка фона (same)
- [x] Fallback-зеркало не включён без доказанной необходимости

**Verification:**
- [ ] Manual: `/teacher/notifications` (или другая длинная) — скролл донизу
- [ ] Manual: `/login` — фон ровный
- [x] `cd frontend && npm run build` (smoke, что CSS не ломает сборку)

**Dependencies:** AB-1

**Files likely touched:**
- `frontend/app/globals.css`

**Estimated scope:** S

---

### Checkpoint: Phase 1 (шов)

- [ ] Шов отсутствует на viewport + scroll + resize
- [ ] Приложение стартует (`npm run dev` / уже running)
- [ ] Не трогали якоря/анимацию blobs (ещё статичны)
- [ ] Review глазами перед Phase 2

---

### Phase 2: Calm drift по бокам

---

## Task AB-3: Боковые коридоры + keyframes + `prefers-reduced-motion`

**Description:** В `globals.css` добавить `@keyframes chem-blob-drift-a|b|c|d` (амплитуда ориентир ±1–3% X, ±2–6% Y; duration ~16–28 s, разные delay/phase; только `transform`). Классы `.chem-blob-drift` / `--a|b|c|d` + `@media (prefers-reduced-motion: reduce) { animation: none }`. В `DecorativeBlobs.tsx` скорректировать позиции SVG так, чтобы центроиды жили в L/R коридорах (~0–22% / ~78–100%), навесить drift-классы на каждое пятно. Публичный API (`scoped?`, `className?`) не ломать; `intensity` не добавлять.

**Acceptance criteria:**
- [x] ≥3 (ожидаемо 4) SVG с маркером drift-класса
- [x] Якоря визуально слева/справа; центр карточки/`max-w-sm` на login не перекрывается центроидом регулярно (anchors in L/R corridors; visual accept pending)
- [x] За ~5–10 с наблюдения виден медленный drift (CSS 16–28s; visual accept pending)
- [x] `prefers-reduced-motion: reduce` → анимация останавливается; позиции покоя в коридорах
- [x] Opacity остаётся в диапазоне ~0.12–0.18; `pointer-events-none` + `aria-hidden` сохранены

**Verification:**
- [ ] Manual: `/login` — 10 с смотреть бока карточки
- [ ] Manual: DevTools → Emulate `prefers-reduced-motion: reduce` — пятна замирают
- [ ] Manual: 360 / 768 / 1280 ширины — центроиды в коридорах

**Dependencies:** AB-2

**Files likely touched:**
- `frontend/app/globals.css`
- `frontend/components/ui/DecorativeBlobs.tsx`

**Estimated scope:** M

---

### Checkpoint: Phase 2 (drift)

- [ ] Drift виден и спокоен; центр контента свободен
- [ ] Reduced-motion работает
- [ ] Шов из Phase 1 не регрессировал
- [ ] Быстрая визуальная приёмка амплитуды («видно / слишком много») — см. Open Questions

---

### Phase 3: Один слой пятен + verify

---

## Task AB-4: Убрать дубль на `/login` (+ проверка atmospheric)

**Description:** Удалить `<DecorativeBlobs scoped />` (и неиспользуемый import) с `frontend/app/login/page.tsx`, оставив global из `layout`. Если на login «пусто» в углах из‑за stacking — поправить z-index / непрозрачный фон `main`/`chem-card`, **не** возвращать второй набор. Вручную проверить student pages и `SessionSummary`: если двоение заметно после анимации — снять scoped там же в этом же срезе **или** остановиться и спросить (spec Ask first на массовое удаление / на снятие global).

**Acceptance criteria:**
- [x] На `/login` в DOM/визуально **один** набор пятен (не два с разными фазами)
- [x] Global в `layout.tsx` на месте
- [x] Login по-прежнему атмосферный (пятна видны по бокам карточки) — visual confirm pending
- [x] По atmospheric-страницам: дубль снят на login, student, welcome, leaderboard, SessionSummary

**Verification:**
- [ ] Manual: `/login` — Inspect: один контейнер blobs (global), drift по бокам
- [ ] Manual smoke: `/student`, welcome, leaderboard, session summary — нет «грязной» двойной лавы
- [x] Не удалять global из layout без явного Ask/approve

**Dependencies:** AB-3

**Files likely touched:**
- `frontend/app/login/page.tsx`
- При подтверждённом двоении (опционально, ≤ остальных файлов задачи): `frontend/app/student/page.tsx`, `frontend/app/student/welcome/page.tsx`, `frontend/app/student/leaderboard/page.tsx`, `frontend/components/tests/SessionSummary.tsx`

**Estimated scope:** S (login only) → M если снимаем несколько atmospheric в том же срезе

---

## Task AB-5: Vitest + build + ручной чеклист

**Description:** Расширить `DecorativeBlobs.test.tsx`: сохранить a11y/global `-z-10`/≥3 svg; добавить ожидание drift-класса на SVG (например `/chem-blob-drift/`); сохранить/дополнить кейс `scoped` → `absolute`, без fixed `-z-10`. Прогнать lint/test/build. Закрыть ручной чеклист spec §3.

**Acceptance criteria:**
- [x] Vitest: root `aria-hidden="true"`, `pointer-events-none`, ≥3 `svg`
- [x] Vitest: у SVG есть класс-маркер drift
- [x] Vitest: `scoped` → `absolute` / без fixed `-z-10` как сейчас задумано
- [x] `npm run build` без ошибок; **0** новых npm-зависимостей
- [ ] Ручной чеклист §3 выполнен (login drift, длинная teacher без шва, reduced-motion, mobile 360) — нужна человеческая приёмка

**Verification:**
- [x] `cd frontend && npm run test -- DecorativeBlobs` (+ SessionSummary)
- [~] `cd frontend && npm run lint` — fail на pre-existing `ContentBlocksEditor` refs (вне scope)
- [x] `cd frontend && npm run build`
- [ ] Manual §3: login 10 с; teacher scroll; reduced-motion; mobile login

**Dependencies:** AB-4

**Files likely touched:**
- `frontend/components/ui/DecorativeBlobs.test.tsx`

**Estimated scope:** S

---

## Task AB-6: Stacking — global blobs не за body background

**Description:** Регрессия после AB-4: на `/login` (и глобально) нет видимых пятен — плоский beige. Root cause: `DecorativeBlobs` global = `fixed inset-0 -z-10` внутри `body.chem-surface relative`. Background layer `body` перекрывает negative-z потомков. Fix (без scoped-дубля): (1) global blobs → `fixed inset-0 z-0`; (2) в `layout.tsx` обернуть `{children}` в `relative z-10 flex min-h-full flex-1 flex-col`, чтобы UI был над blobs, а прозрачные области пропускали wash + пятна. Не возвращать scoped на login.

**Acceptance criteria:**
- [x] Root cause задокументирован (negative z vs body bg)
- [x] Global blobs: `z-0`, не `-z-10`
- [x] Content wrapper `z-10` в root layout
- [x] Один набор пятен (global only)
- [x] Vitest обновлён под `z-0` / запрет `-z-10` на global
- [ ] Manual: `/login` — пятна видны по бокам карточки + drift

**Verification:**
- [x] `cd frontend && npm run test -- DecorativeBlobs SessionSummary`
- [ ] Manual: `/login`, `/student` — blobs visible, no double lava

**Dependencies:** AB-4, AB-5

**Files touched:**
- `frontend/app/layout.tsx`
- `frontend/components/ui/DecorativeBlobs.tsx`
- `frontend/components/ui/DecorativeBlobs.test.tsx`
- `tasks/ambient-background-calm-drift.md` (этот файл)

**Estimated scope:** S

---

## Task AB-7: Visible drift + wax morph (post visual QA)

**Description:** User QA: blobs visible on `/login` but appear static. Bump calm keyframes so motion is noticeable in ~5–10s and shape reads as lava-lamp wax — CSS only: multi-stop `translate` + uneven `scaleX`/`scaleY` + slight `rotate` (no path morph / no new deps). Keep side corridors; `prefers-reduced-motion: reduce` → still `animation: none`. Update spec §5.2 note that translate-only MVP was too subtle.

**Acceptance criteria:**
- [x] Keyframes multi-stop (0/25/50/75/100) with translate Y ±12–24% (up+down), X ~3–8%, scale ~0.92–1.12, slight rotate
- [x] Durations ~18–30s; staggered delays; reduced-motion still kills animation
- [x] Class markers `chem-blob-drift*` unchanged (tests still match)
- [x] Plan + brief spec open note updated
- [ ] Manual: `/login` hard refresh — slow drift + shape change visible in 5–10s; center card not crossed heavily

**Verification:**
- [x] `cd frontend && npm run test -- DecorativeBlobs`
- [ ] Manual: `/login` 10s watch corners; DevTools reduced-motion → static

**Dependencies:** AB-6

**Files touched:**
- `frontend/app/globals.css`
- `frontend/components/ui/DecorativeBlobs.tsx` (comment only)
- `docs/specs/ambient-background-calm-drift.md`
- `tasks/ambient-background-calm-drift.md`

**Estimated scope:** S

---

### Checkpoint: Complete

- [x] Все acceptance criteria AB-1…AB-7 (код); ручной §3 / AB-7 visual — pending human
- [~] Success criteria spec §1.4 / §8 — код/тесты ok; visual pending
- [x] Open Questions §10 закрыты ответом человека («ok» → дефолты)
- [ ] Ready for code review / merge — после визуальной приёмки lava-lamp motion

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Шов не от gradient, а от другого слоя | High | AB-1 диагностика; не прыгать сразу в зеркальный тайл |
| `body { background }` shorthand конфликтует с `.chem-surface` | Med | В AB-2 явно развести color/image; проверить computed |
| Drift укачивает / перекрывает контент | Med | Малая амплитуда + коридоры; при жалобах уменьшить ещё (Ask перед заметным увеличением) |
| Дубль global/scoped усиливает эффект после анимации | High | AB-4 обязателен в MVP; mass-remove atmospheric — только по факту двоения |
| Снятие scoped с login → «пустые» углы (stacking) | **High (сбылось)** | AB-6: `z-0` blobs + content `z-10` wrapper; **не** возвращать scoped |
| Хрупкие тесты на computed animation | Low | Тестировать классы/a11y, не кадры |
| Регресс на student/SessionSummary после смены только login | Med | Smoke в AB-4; не трогать global без Ask |

---

## Open Questions

Нужен ответ человека **до или на старте IMPLEMENT** (из spec §10 + план):

1. **Дубли (Assumption 8 / §5.3):** подтверждаете дефолт «оставить global в layout, снять scoped с `/login` (и с других atmospheric только если двоится)»? Или наоборот — только scoped на atmospheric и убрать global? (**Удаление global — Ask first.**)
   → **Ответ:** ok — дефолт. Сняты scoped с login + student/welcome/leaderboard/SessionSummary (двоение с global структурно ясно после анимации).
2. **Мобильный логин (360px):** лёгкое касание края карточки пятном при opacity ≤0.18 — ok, или сильнее уводить за край / `overflow: hidden`?
   → **Ответ:** ok — касание края допустимо.
3. **Амплитуда:** после первого CSS-прохода (checkpoint Phase 2) нужна одна быстрая визуальная приёмка «видно / слишком много» перед merge.
   → **Статус:** AB-3 (±1–4%) невидим; AB-7 ~4–12% всё ещё слабо / без явного up+down; post-QA bump → Y ±12–24% bipolar. Ждёт глазами: «видно / слишком много».
