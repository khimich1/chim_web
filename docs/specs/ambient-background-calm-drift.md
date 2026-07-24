# Spec: Спокойный «живой» фон (calm drift)

**Версия:** 0.2.0  
**Дата:** 2026-07-24  
**Статус:** draft (ждёт ревью)  
**Идея:** [`docs/ideas/ambient-background-calm-drift.md`](../ideas/ambient-background-calm-drift.md)  
**Scope:** только фон — бесшовный `.chem-surface` + тихое плавание `DecorativeBlobs` **по бокам**. Без смены палитры UI, без новых зависимостей, без правок форм/списков/навигации.

**Скриншоты-ориентиры (из ревью):**

1. Teacher-страница — горизонтальная полоса на фоне («убрать полосу»).
2. `/login` — зелёная разметка по бокам карточки («пускай будут плавать по бокам»).

---

## Assumptions (проверьте до PLAN/IMPLEMENT)

Если не поправите — считаем принятыми:

1. **Одна спокойная интенсивность везде** — учитель и ученик; отдельных «игровых» режимов нет.
2. **Причина полосы** — слой фона (`.chem-surface` на `body` и/или стык `html`/`body`), не контентный блок. Стратегия: сначала непрерывный wash (`background-repeat: no-repeat`, `background-size: 100% 100%`, при необходимости мягкие стопы и фон на `html`). **Зеркалирование градиента** — только fallback, если шов останется после этого.
3. **Пятна** — текущие SVG в `DecorativeBlobs`, цвета `--blob-teal|slate|amber|peach|sage`. Opacity **0.12–0.18** (не ярче текущего).
4. **Боковые коридоры** — якоря и drift остаются в полосах примерно **0–22%** и **78–100%** ширины viewport. Центр (~середина, карточка `max-w-sm` на логине, колонки контента) **не** должен регулярно перекрываться центроидом пятна. Основное движение — **по вертикали**; по горизонтали — люфт внутри коридора (см. §5.2).
5. **Темп** — циклы **18–30 с**, у каждого пятна свой `animation-duration` и `animation-delay`, чтобы не синхронно «дышали». Амплитуда спокойная, но **заметно видимая** за 5–10 с: ориентир **Y ±12–24%** / **X ~3–8%** translate (явный вверх–вниз за цикл) + squash/stretch scale **~0.92–1.12** + лёгкий rotate (AB-7 post-QA; ранний ±1–4%, затем ~4–12% Y без биполярного хода были слишком тихими).
6. **`prefers-reduced-motion: reduce`** — `animation: none` на всех drift-классах; позиции остаются «покоящимися» в боковых якорях; шов по-прежнему отсутствует.
7. **Слои / a11y** — `pointer-events-none`, `aria-hidden="true"`, под UI (`fixed -z-10` global / `absolute z-0` scoped) — как сейчас.
8. **Дубль global + scoped** — сейчас scoped на: `/login`, `/student`, `/student/welcome`, `/student/leaderboard`, `SessionSummary`. Плюс всегда global из `layout`. **В этом срезе на `/login` убрать визуальный дубль** (предпочтение: оставить **scoped** на login, т.к. он привязан к `main`; global на этой странице не должен давать второй набор анимированных пятен). На остальных scoped-страницах — то же правило или проверка «не двоится»; если сомнение — спросить перед массовым удалением.
9. **Backend / API / E2E auth flows** не трогаем (кроме визуальной ручной проверки логина).

→ Поправьте п.4 (ширина коридоров), п.5 (амплитуда) или п.8 (политика дублей), если хотите иначе.

---

## 1. Objective

### 1.1 Проблема

- На фоне видна **горизонтальная полоса** (резкий стык оттенков), в т.ч. она может **резать** декоративное пятно — фон выглядит сломанным.
- Пятна уже есть, но **стоят на месте**. Нужно ощущение тихой лава-лампы **по бокам**, особенно заметное на просторном `/login`, без движения через карточку и текст.

### 1.2 HMW

> Как пользователь, я хочу ровный тёплый фон без шва и едва заметные пятна, которые медленно плавают слева и справа от контента, чтобы интерфейс был живым, но не отвлекал от работы.

### 1.3 User stories

| ID | Story | Принятие |
|----|-------|----------|
| US-BG-1 | Как любой пользователь, я не вижу горизонтального шва на фоне при любой высоте страницы и при скролле | Нет видимой линии/стыка оттенков на фоне |
| US-BG-2 | Как гость на `/login`, я вижу, что пятна тихо плывут **по бокам** карточки «Вход» | Drift виден за ~5–10 с наблюдения; карточка не «ездит» под пятнами |
| US-BG-3 | Как учитель на длинной странице, я не отвлекаюсь на фон во время чтения списка | Пятна только у краёв; контраст низкий |
| US-BG-4 | Как пользователь с reduced-motion, я вижу статичный бесшовный фон | Нет CSS-анимации drift |

### 1.4 Success criteria (тестируемые)

- [ ] Viewport и страница с длинным скроллом: **нет** горизонтальной полосы/шва на фоне (в т.ч. пятно не «обрезано» линией стыка).
- [ ] `/login`: ≥3 пятна; якоря слева/справа; за 10 с наблюдения виден медленный drift; центр карточки свободен от центроида пятна.
- [ ] Teacher-страница с контентом: drift боковой, низкоконтрастный; шапка/текст читаемы.
- [ ] Emulate `prefers-reduced-motion: reduce` → анимация останавливается; шов отсутствует.
- [ ] Root `DecorativeBlobs`: `aria-hidden="true"`, класс с `pointer-events-none`.
- [ ] На `/login` после фикса дубля — **один** набор пятен (не два перекрывающихся слоя с разными фазами).
- [ ] `npm run test -- DecorativeBlobs` зелёный; `npm run build` без ошибок; **0** новых npm-зависимостей.

---

## 2. Tech Stack

| Что | Выбор |
|-----|--------|
| UI | Next.js App Router (frontend) |
| Стили | CSS в `globals.css` + Tailwind-классы позиций на SVG |
| Анимация | Только CSS `@keyframes` / `animation` |
| Тесты | Vitest + Testing Library |
| Запрещено для MVP | framer-motion, GSAP, canvas, WebGL, новые пакеты |

---

## 3. Commands

```bash
cd frontend
npm run dev
npm run test -- DecorativeBlobs
npm run lint
npm run build
```

**Ручной чеклист**

1. Открыть `/login` — 10 с смотреть бока карточки.  
2. Открыть длинную teacher-страницу (например `/teacher/notifications`) — проскроллить донизу, искать шов.  
3. DevTools → Rendering → **Emulate CSS media feature `prefers-reduced-motion: reduce`** → обновить/переключить — пятна замирают.  
4. Узкий mobile viewport на `/login` — пятна не залезают заметно на поля формы (допустимо лёгкое касание краёв карточки с очень низкой opacity).

---

## 4. Project Structure

### 4.1 Файлы в scope

| Файл | Роль |
|------|------|
| `frontend/app/globals.css` | `.chem-surface` бесшовный; `@keyframes` drift; `@media (prefers-reduced-motion)` |
| `frontend/components/ui/DecorativeBlobs.tsx` | Якоря в коридорах; классы `chem-blob-drift*` на SVG |
| `frontend/components/ui/DecorativeBlobs.test.tsx` | a11y + наличие/наличие drift-классов |
| `frontend/app/login/page.tsx` | Убрать дубль с global (см. §5.3) |
| При необходимости: другие scoped-страницы / `layout.tsx` | Согласовать один слой пятен |

### 4.2 As-is монтирование `DecorativeBlobs`

| Место | Режим | Заметка |
|-------|--------|---------|
| `app/layout.tsx` | global `fixed` | На **всех** страницах |
| `app/login/page.tsx` | scoped | **Дубль** с layout |
| `app/student/page.tsx` | scoped | Дубль |
| `app/student/welcome/page.tsx` | scoped | Дубль |
| `app/student/leaderboard/page.tsx` | scoped | Дубль |
| `components/tests/SessionSummary.tsx` | scoped | Дубль внутри summary UI |

### 4.3 Вне scope

Backend, палитра карточек/кнопок, `TeacherNav`, контент форм, замена SVG-path на другие формы «ради красоты».

---

## 5. Поведение и Code Style

### 5.1 Бесшовный фон (`.chem-surface`)

**Сейчас:**

```css
.chem-surface {
  background: linear-gradient(
    165deg,
    color-mix(in srgb, var(--chem-band) 28%, var(--chem-bg)) 0%,
    var(--chem-bg) 55%
  );
}
```

**Целевое поведение:**

- Градиент **покрывает всю площадь** элемента фона без тайла.
- На высоких документах нет второй «копии» wash и нет горизонтального стыка.
- При необходимости задать тот же `--chem-bg` (или тот же wash) на `html`, чтобы под/за `body` не выглядывал другой цвет.

**Минимальный целевой паттерн (имена/стопы можно уточнить в IMPLEMENT):**

```css
html {
  background-color: var(--chem-bg);
}

.chem-surface {
  background-color: var(--chem-bg);
  background-image: linear-gradient(
    165deg,
    color-mix(in srgb, var(--chem-band) 28%, var(--chem-bg)) 0%,
    var(--chem-bg) 52%,
    var(--chem-bg) 100%
  );
  background-repeat: no-repeat;
  background-size: 100% 100%;
}
```

**Диагностика перед/после (IMPLEMENT):**

1. На странице с швом в DevTools посмотреть computed `background` у `html`, `body`, и нет ли лишнего wrapper с другим bg.  
2. Временно отключить `DecorativeBlobs` — если полоса осталась, виноват surface/html; если пропала — искать клип/слой blobs.  
3. После фикса — скролл + resize окна; шов не должен появляться на 50%/100%/150% высоты.

**Fallback (только если шов жив):** симметричный (зеркальный) multi-stop wash или `background-attachment` — зафиксировать выбранный вариант комментарием *why* в CSS и кратко в PR.

### 5.2 Боковые коридоры и drift

```
Viewport width
|<-- L corridor -->|<----- safe center ------>|<-- R corridor -->|
0%              ~22%                         ~78%             100%
     пятна L                                      пятна R
              карточка / main content здесь
```

**Правила раскладки (4 пятна, как сейчас):**

| # | Цвет (токен) | Коридор | Якорь (ориентир) | Drift-профиль |
|---|--------------|---------|------------------|---------------|
| 1 | `--blob-teal` | L | верх–лево, частично за краем | медленный вниз–вверх, duration ~22s |
| 2 | `--blob-slate` | L | низ–лево | другой phase/delay, ~26s |
| 3 | `--blob-amber` | R | середина–право | ~18s |
| 4 | `--blob-peach` | R | низ–право | ~24s |

Допустимо слегка скорректировать `top`/`left`/`right`/`bottom` vs текущих `-left-16` / `-right-12` и т.д., **чтобы центроиды жили в коридорах**, а не уезжали под карточку на типичных ширинах (360px, 768px, 1280px).

**Анимация:**

- Класс-маркер на каждом SVG, например `chem-blob-drift chem-blob-drift--a|b|c|d`.
- Только `transform` (translate + uneven `scaleX`/`scaleY` + лёгкий `rotate` для wax-morph); **не** анимировать `top`/`left` (дороже и дёрганее). Path-`d` morph / SMIL — не нужны для MVP.
- Multi-stop keyframes (`0/25/50/75/100%`), не только 0/50/100 — иначе «качается туда-сюда», а не «воск».
- После visual QA (AB-7 + amplitude bump): Y translate **±12–24%** от box (оба знака за цикл — вверх и вниз), X **~3–8%**; scale **~0.92–1.12**. Раньше ±1–4%, затем ~4–12% в основном в одну сторону по Y — всё ещё слабо.
- `animation-timing-function: ease-in-out`; `animation-iteration-count: infinite`; циклы **~18–30 с**.
- Не использовать JS `requestAnimationFrame`.

**Open note (post-QA):** translate-only MVP из раннего §5.2 оказался visually silent; ship — CSS transform morph (squash/stretch), без новых deps. См. plan AB-7.

**Пример keyframes (амплитуду подкрутить глазами):**

```css
@keyframes chem-blob-drift-a {
  0%,
  100% {
    transform: translate(0, 0) scale(1, 1) rotate(0deg);
  }
  25% {
    transform: translate(5%, -18%) scale(1.08, 0.94) rotate(3deg);
  }
  50% {
    transform: translate(4%, 22%) scale(0.94, 1.1) rotate(-2deg);
  }
  75% {
    transform: translate(7%, -14%) scale(1.06, 0.96) rotate(2deg);
  }
}

.chem-blob-drift--a {
  animation: chem-blob-drift-a 22s ease-in-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  .chem-blob-drift {
    animation: none !important;
  }
}
```

### 5.3 Дубль global vs scoped

**Проблема:** `layout` всегда рисует global `fixed` blobs; `/login` рисует ещё scoped → два набора с анимацией = грязнее и ярче, чем «спокойно».

**Решение для MVP (принято в Assumptions п.8):**

- На страницах, где уже есть **scoped** `DecorativeBlobs` внутри своего `relative` контейнера, **не показывать второй набор**.
- Практичный путь A (предпочтителен для login): оставить scoped на странице; **скрыть global**, когда страница сама рисует blobs — например prop/флаг сложно без context; проще: **убрать `<DecorativeBlobs />` из `layout`** и гарантировать blobs на нужных оболочках **или** убрать scoped с login и полагаться только на global.

**Выбранный дефолт для IMPLEMENT (если не поправят Assumption):**

1. **Оставить global в `layout`** (единый фон для всего приложения — главное место анимации).  
2. **Удалить scoped `<DecorativeBlobs scoped />` с `/login`** (и при ручной проверке — с student pages / SessionSummary, если видно двоение).  
3. Если на login без scoped «пусто» в углах из‑за stacking — чинить z-index/фон `main`, а не возвращать второй набор.

Альтернатива (спросить, если A даёт регресс на login): оставить только scoped на atmospheric-страницах и убрать global — **Ask first**, т.к. меняет все роуты без собственного scoped.

### 5.4 Компонент (ориентир API)

Публичный API **не обязателен** менять. Если понадобится:

```tsx
type DecorativeBlobsProps = {
  className?: string;
  /** absolute в relative-родителе вместо fixed на viewport */
  scoped?: boolean;
};
```

Prop `intensity` в MVP **не добавляем** (дефолт = calm).

---

## 6. Testing Strategy

| Уровень | Что проверяем |
|---------|----------------|
| Vitest | Root: `aria-hidden="true"`, `pointer-events-none`, ≥3 `svg` |
| Vitest | У SVG (или root children) есть класс-маркер drift (например `/chem-blob-drift/`) |
| Vitest | `scoped` → классы `absolute` / без `-z-10` fixed (сохранить текущие ожидания + не сломать) |
| Manual | §3 чеклист: шов, боковой drift на login, reduced-motion, нет дубля на login |
| Build | `npm run build` |

**Не требуем:** pixel-diff, Playwright на анимацию (хрупко), backend-тесты.

---

## 7. Boundaries

**Always**

- Низкая opacity; медленный drift; коридоры по бокам.
- `prefers-reduced-motion` выключает анимацию.
- Сначала доказать исчезновение шва на длинной странице, потом полировать амплитуду.
- Прогнать `DecorativeBlobs` tests + build перед merge.

**Ask first**

- Удаление **global** blobs из `layout` (вместо удаления scoped).
- Смена SVG на blur-orbs / canvas.
- Prop `intensity` или разные пресеты по роутам.
- Амплитуда / morph сверх «lava lamp whisper» (disco, path-morph libs). AB-7: ±1–4% → ~4–12% → post-QA Y ±12–24% с явным up/down + squash/stretch — дальше только по новой жалобе.

**Never**

- Пятна, регулярно пересекающие центр карточки/таблицы.
- Новые animation-библиотеки.
- Анимация, ломающая клики (всегда `pointer-events-none`).
- Коммит с оставшимся видимым швом «потом поправим».

---

## 8. Success Criteria (сводка)

1. Нет горизонтального шва (viewport + scroll + resize).  
2. Пятна тихо плавают **по бокам** (лава-лампа «на шёпоте»).  
3. На `/login` один набор пятен, карточка в safe center.  
4. Reduced-motion → статика.  
5. Тесты + build зелёные; без новых deps.

---

## 9. Out of Scope / Not Doing

| Не делаем | Почему |
|-----------|--------|
| Зеркальный тайл как **первый** фикс | Симптом; сначала no-repeat / full-size / html bg |
| Заметная лава-лампа | «Спокойно везде» |
| Dual intensity | Отклонено в idea-refine |
| Canvas / metaballs / turbulence | Overkill, perf, сложность a11y |
| Смена warm-paper палитры | Вне запроса |
| Parallax от скролла / мыши | Другая фича, шумнее |

---

## 10. Open Questions

1. **Дубли (уточнение к Assumption 8):** ок ли дефолт «оставить global, снять scoped с login (и других atmospheric, если двоится)»? Или наоборот — только scoped на atmospheric и убрать global?
2. **Мобильный логин:** если на 360px коридоры узкие и пятна касаются карточки краем — это ok при opacity ≤0.18, или нужно сильнее уводить за `overflow: hidden` края?
3. **Амплитуда:** после первого CSS-прохода нужна одна быстрая визуальная приёмка («видно / слишком много») перед merge.

---

## 11. Implementation order

| Шаг | Что | Verify |
|-----|-----|--------|
| 1 | Диагностика шва (html/body/blobs) | Понятна причина |
| 2 | Фикс `.chem-surface` (+ html bg при нужде) | Длинная страница без полосы |
| 3 | Якоря blobs в коридорах + keyframes + reduced-motion | `/login` drift по бокам |
| 4 | Убрать дубль на `/login` (и др. по факту) | Один набор пятен |
| 5 | Vitest + build + ручной reduced-motion | Критерии §1.4 |

Каждый шаг — тонкий вертикальный срез; не смешивать фикс шва и большой рефактор монтирования в одном непроверенном коммите без verify.

---

## 12. Риски

| Риск | Митигация |
|------|-----------|
| Шов не от gradient, а от другого слоя | Шаг диагностики §5.1 |
| Drift укачивает / отвлекает | Малая амплитуда + reduced-motion; при жалобах уменьшить ещё |
| Дубль global/scoped усиливает эффект | §5.3 обязательно в том же MVP |
| Хрупкие тесты на computed animation | Тестировать классы/a11y, не кадры анимации |
