# CRO Analysis: /zapis (himych.ru)

**Дата:** 29.07.2026  
**Scope:** Recommended (full analysis + copy alternatives + test ideas)  
**Skills:** `mkt-workflow-cro-page`, `mkt-page-cro`  
**Baseline conversion:** ⚠️ NOT AVAILABLE (нет подключённой Метрики / GA в агенте)  
**Benchmark:** landing paid traffic — average 2–5%, good 5–10% ([mkt-page-cro checklist])

## Configuration

| Parameter | Value |
|-----------|-------|
| Page | `frontend/app/(marketing)/zapis/page.tsx` |
| Type | Landing (campaign) |
| Goal | Lead capture → бесплатная диагностика 30 мин |
| Traffic | VK Ads (primary), SEO organic, Telegram |
| Audience | Родители 10–11 кл, РФ, онлайн |

---

## Executive Summary

Страница **хорошо структурирована** и совпадает со спекой `tilda-landing-vk-ads.md` по текстам и блокам. Главные потери конверсии — не copy, а **доверие и message match**: нет фото преподавателя, нет блока «платформа» со скрином, отзывы без лиц, header отвлекает на `/ceny`, `/blog`, login. Hero для VK холодного трафика **слишком SEO-универсален** — не бьёт в страх родителя «не сдаст ЕГЭ».

**Оценка потенциала:** quick wins (1–2 дня) могут дать +15–30% к form submit при текущем нулевом baseline; high-impact (фото + платформа) — ещё +10–20%.

---

## Conversion Scorecard

| Element | Score | Status | Rationale |
|---------|-------|--------|-----------|
| Value Proposition | 7/10 | 🟡 | Понятно за 5 сек, но benefit generic («репетитор по химии») |
| Headline | 6/10 | 🟡 | SEO ✅, VK pain ❌ — нет outcome/страха |
| CTA | 8/10 | 🟢 | Форма above fold, кнопка «Записаться на диагностику», microcopy ok |
| Visual Hierarchy | 7/10 | 🟡 | Логичный scroll, но нет hero visual |
| Trust Signals | 5/10 | 🔴 | Текстовые отзывы, нет фото, нет скрина платформы |
| Objection Handling | 8/10 | 🟢 | FAQ сильный (бесплатно, Умскул, онлайн) |
| Friction | 6/10 | 🟡 | 4 обяз. поля + checkbox ok; nav и TG/VK конкурируют с формой |
| Message Match (VK) | 5/10 | 🔴 | H1 ≠ типичный ad hook; нет UTM-aware hero |

**Overall:** 6.5/10 — solid MVP landing, not yet optimized for paid cold traffic.

---

## What's Working

1. **Форма в hero** — grid 2 col desktop, form first on mobile intent ✅
2. **CTA copy** — «Записаться на диагностику», не «Отправить» ✅
3. **Risk reversal** — «Без обязательств», FAQ про бесплатность ✅
4. **Specificity** — 30 мин, 70+/80+, 2 500 ₽/1 500 ₽ прозрачно ✅
5. **Dual form** — hero + footer CTA на длинном scroll ✅
6. **UTM capture** — `LeadForm` читает utm_* из URL ✅
7. **Success state** — fallback Telegram после submit ✅

---

## Top 5 Issues (Priority)

| # | Issue | Impact | Effort | Fix |
|---|-------|--------|--------|-----|
| 1 | **Нет фото преподавателя в hero** | High | Low | Портрет рядом с H1 или над формой — доверие для cold VK |
| 2 | **Отсутствует блок «Платформа»** (скрин + 4 пункта) | High | Med | Секция из spec §блок 4 — diff vs Умскул/репетиторы |
| 3 | **Header отвлекает** (Цены, Блог, Login) | Med | Low | На `/zapis` — minimal header: logo + «Записаться» |
| 4 | **H1 SEO-first, не pain-first** для VK | High | Low | UTM/vk variant hero или subhead с pain |
| 5 | **Отзывы без фото/города** | Med | Low | 1 фото + «Москва» где ok; иначе — initials avatar |

---

## Quick Wins (Implement Now)

### 1. Minimal header на landing `/zapis`

Сейчас `MarketingHeader` ведёт на `/ceny`, `/blog` (возможно 404) и «Вход для учеников».

**Fix:** layout variant или prop `minimal` — только logo + anchor `#form`.

**Expected:** −5–15% bounce от lost navigation (industry pattern для paid LP).

### 2. Pain-driven subhead для VK

Текущий subhead feature-heavy. Добавить строку под H1:

```
Если химия — слабое место и до ЕГЭ меньше года, за 30 минут поймём, 
что успеть и с чего начать — без давления записываться дальше.
```

**Expected:** message match с ad « боитесь не сдать? ».

### 3. Убрать TG/VK под hero-формой (A/B)

`showSocialLinks={false}` уже на footer-form. На hero — **конкурирует** с submit.

**Fix:** hero `showSocialLinks={false}`; TG только в success state + footer.

### 4. Микро-trust рядом с формой

Под заголовком формы (если добавить):

```
✓ Бесплатно · 30 мин · без обязательств
✓ Перезвоним за 2 часа
```

### 5. Schema.org FAQ

`FAQPage` JSON-LD из `FAQ_ITEMS` — rich snippets в Яндекс/Google, +CTR organic.

---

## High-Impact Changes (Prioritize)

### 1. Hero visual — фото + optional platform thumb

Spec требует портрет. Без лица cold traffic trust −20–40% (education services norm).

```
[Фото] + H1 + bullets | [Form]
```

### 2. Блок «Платформа» (missing vs spec)

Между «Диагностика» и «Форматы и цены»:

**H2:** `Между занятиями ребёнок не «забывает»`

- Скрин ЛК (blur sensitive data)
- 4 bullets: учебник, тесты ЕГЭ, ДЗ, прогресс для родителя
- Micro-CTA → `#form`

**Why:** ключевой diff vs «просто репетитор в Zoom».

### 3. Sticky mobile CTA

После scroll past hero — fixed bottom bar:

```
[ Записаться на диагностику ]  → #form
```

VK 70%+ mobile; второй шанс конверсии.

### 4. Pricing placement test

Цены **до** final CTA могут вызвать sticker shock на cold traffic.

**Hypothesis:** move pricing below FAQ or collapse «от 1 500 ₽» в одну строку в hero.

### 5. VK-specific landing variant

`/zapis?utm_source=vk` → swap hero:

| Element | SEO default | VK variant |
|---------|-------------|------------|
| H1 line 2 | Бесплатная диагностика 30 минут | Узнайте за 30 минут, успеет ли ребёнок к 70+ |
| Kicker | Онлайн по всей России | Для родителей 10–11 класса |

---

## Copy Alternatives

### Headline (H1)

**Current:**
> Репетитор по химии ЕГЭ и ОГЭ  
> Бесплатная диагностика 30 минут

**Alt A — Pain (VK):**
> Химия на ЕГЭ пугает?  
> Бесплатно разберём уровень за 30 минут

**Alt B — Outcome:**
> Подготовка к ЕГЭ по химии с планом на весь год  
> Начните с бесплатной диагностики

**Alt C — Diff (current SEO, sharpened):**
> Репетитор по химии — не поток, а ваш ребёнок  
> Диагностика 30 мин · платформа с ДЗ между уроками

*Recommend:* SEO → C; VK ads → A; test B for parents who already search «репетитор».

### CTA Button

**Current:** Записаться на диагностику ✅ (keep)

**Alt:** Получить бесплатный разбор уровня  
**Alt:** Записать ребёнка на 30 мин — бесплатно

### Final CTA section

**Current:** Запишитесь на диагностику — 30 минут, бесплатно

**Alt:** Остались вопросы? Запишитесь — разберём за 30 минут бесплатно

---

## Psychology Applied

| Principle | Current | Recommendation |
|-----------|---------|----------------|
| **Loss aversion** | Weak | «До ЕГЭ X месяцев — успеем ли?» в VK hero |
| **Social proof** | Text quotes | Photo + specific result (3→5) ✅ already in quote |
| **Risk reversal** | Strong | FAQ + «без обязательств» — keep prominent |
| **Authority** | 8 лет, 100+ | Add credentials line (вуз, стаж) if true |
| **Specificity** | 30 min, 70+/80+ | Keep; add exam year «ЕГЭ 2026» |
| **Contrast** | vs Умскул in FAQ | Move one line to hero: «не поток на 500» |

---

## Test Ideas (A/B)

| Test | Hypothesis | Metric | Min sample |
|------|------------|--------|------------|
| Hero H1 pain vs SEO | Pain +8–15% CR on VK | form_submit | 200 sessions/arm |
| Photo vs no photo | Photo +10–20% CR | form_submit | 150/arm |
| Hero TG links on/off | Off +5% form submit | form_submit | 100/arm |
| Pricing above/below FAQ | Below +5% on cold | form_submit | 200/arm |
| Sticky mobile CTA | +8% mobile CR | form_submit mobile | 150/arm |

Run setup: `mkt-workflow-test-ab-setup`. Track: Яндекс.Метрика goal `form_submit`.

---

## Friction Audit (Form)

| Field | Required | Verdict |
|-------|----------|---------|
| Имя | yes | Keep |
| Телефон | yes | Keep; consider mask +7 |
| Класс | yes | Keep — segmentation |
| Цель | yes | Keep |
| Комментарий | no | **Remove on VK variant** (optional adds cognitive load) |
| Privacy checkbox | yes | Keep (152-ФЗ) |

Form field count: **4 required** — within benchmark (≤5 for lead gen).

Separate deep dive: `mkt-workflow-cro-form`.

---

## Gap vs Spec (tilda-landing-vk-ads.md)

| Block | Spec | Current | Status |
|-------|------|---------|--------|
| 1 Hero + form | ✅ | ✅ | Match |
| 2 Social proof | ✅ | ✅ partial (no photos) | 🟡 |
| 3 Диагностика | ✅ | ✅ | Match |
| 4 **Платформа** | ✅ | ❌ missing | 🔴 |
| 5 Цены | ✅ | ✅ | Match |
| 6 О преподавателе | ✅ | ✅ (no photo) | 🟡 |
| 7 FAQ | ✅ | ✅ | Match |
| 8 Final CTA | ✅ | ✅ | Match |
| Minimal nav for ads | ✅ | ❌ full header | 🔴 |

---

## Implementation Roadmap

### Week 1 (quick wins)
- [ ] Minimal header on `/zapis`
- [ ] Hero `showSocialLinks={false}`
- [ ] Pain subhead or VK utm variant
- [ ] Trust microcopy above form
- [ ] FAQ schema.org

### Week 2 (high impact)
- [ ] Hero photo
- [ ] Platform section + screenshot
- [ ] Review photos/avatars
- [ ] Sticky mobile CTA
- [ ] Метрика: goal `form_submit`

### Week 3 (test)
- [ ] A/B H1 pain vs SEO on VK traffic
- [ ] Run `mkt-workflow-campaign-analyze` after 2 weeks ads

---

## Next Steps

1. **Form CRO:** `mkt-workflow-cro-form` — поля, validation, mobile UX
2. **A/B plan:** `mkt-workflow-test-ab-setup` — H1 + photo tests
3. **VK creatives:** `mkt-workflow-content-ads` — message match с winning hero
4. **Re-audit:** через 4 недели после изменений + baseline из Метрики

---

## Unresolved Questions

1. Подключена ли Яндекс.Метрика на prod? (baseline ⚠️ NOT AVAILABLE)
2. Есть ли готовое фото и скрин платформы для блока 4?
3. Страницы `/ceny`, `/blog` — live или 404? (влияет на header fix)
4. Будет ли отдельный `/gruppa-ege` для VK креатива B?
