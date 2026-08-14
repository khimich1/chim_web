# Campaign Plan: Набор авг–окт 2026 (Химыч)

**Дата:** 29.07.2026  
**Skill:** `mkt-workflow-campaign-plan`  
**Scope:** Recommended (timeline, budget, content, risks)  
**Stakeholder:** solo (Роман) — approve self

---

## Campaign Configuration

| Parameter | Value |
|-----------|-------|
| **Campaign name** | Набор ЕГЭ/ОГЭ — август–октябрь 2026 |
| **Goal** | Lead generation → бесплатная диагностика → платящие ученики |
| **Audience** | New prospects: родители 10–11 кл, РФ, онлайн |
| **Budget (Base)** | **135 000 ₽** ads + **~18 000 ₽** infra/misc = **~153 000 ₽** |
| **Timeline** | **15.08.2026** – **31.10.2026** (VK с 15.08; прогрев с 29.07) |
| **Channels** | VK Ads, Яндекс Direct (с сен), SEO/TG organic, Profi.ru |
| **Landing** | `himych.ru/zapis` (diag), `/gruppa-ege` (group) |
| **CRM** | Google Sheet + backend leads API |

**Связано:** [plan-3months-ads](../pm/plan-3months-ads-2026-08-10.md), [brand-context](../brand-context.md), [CRO audit](../cro/zapis-analysis.md), [SEO audit](../seo/audits/himych-audit-2026-07-29.md)

---

## Executive Summary

Трёхмесячная кампания набора учеников на **solo-репетитора по химии** с поэтапным масштабированием: **VK pilot (авг)** → **VK + Direct (сен)** → **оптимизация + SEO (окт)**.

**SMART-цель к 31.10.2026:**
- **~98 лидов** (83 paid + 15 organic)
- **12–15 новых платящих** учеников
- **CPL VK ≤1 500 ₽**, blended CAC ads **~11–13k ₽**
- **≥45% лидов** не с Profi.ru (окт)

**Baseline performance:** ⚠️ NOT AVAILABLE — первый запуск, нет GSC/Метрики history.

---

## Audience & Personas

### Primary: Родитель 11 класса

| | |
|---|---|
| **JTBD** | Найти репетитора, успеть к ЕГЭ по химии |
| **Боли** | «Не сдаст», хаос в подготовке, непонятно с чего начать |
| **Триггеры** | Плохая оценка, августовские переживания, соседи нашли репетитора |
| **Возражения** | Дорого, онлайн не работает, «ещё рано», страх давления на ребёнка |
| **Где ловить** | VK (родители 35–50), поиск Яндекс, TG-каналы ЕГЭ, Profi |

### Secondary: Родитель 10 класса / группа

| | |
|---|---|
| **JTBD** | Начать системно, не переплачивать за индивидуалку |
| **Оффер** | Группа 4–6 чел, 1 500 ₽/чел × 2 ч, старт 1 сентября |
| **Landing** | `/gruppa-ege` (E6) |

---

## Funnel & Touchpoints

```
AWARENESS          CONSIDERATION         CONVERSION           RETENTION
─────────────────────────────────────────────────────────────────────────
VK Ads / Direct    Landing /zapis        Форма → Sheet       Пробное 30 мин
TG / VK organic    FAQ, отзывы           Контакт <2ч         Оплата → app
SEO (окт+)         /gruppa-ege           Telegram fallback   E2 bundle (+500)
Profi.ru           Profi → TG/zapis      Диагностика         Referral
```

| Stage | KPI | Target (Base) |
|-------|-----|---------------|
| Click → Lead | Landing CR | 8–12% (cold VK) |
| Lead → Contact | Response <2h | 65% |
| Contact → Trial | Diagnostic booked | 55% |
| Trial → Paid | Conversion | 45% |
| **Lead → Paid** | End-to-end | **~14–16%** |

---

## Messaging Framework

### Pillars (не менять между каналами)

1. **Бесплатная диагностика 30 мин** — без обязательств, честный уровень
2. **Не поток** — живой репетитор, программа на год, 4–6 в группе max
3. **Платформа между уроками** — ДЗ, тесты, прогресс (diff vs Zoom-only)

### По каналам

| Channel | Hook | CTA |
|---------|------|-----|
| VK Ads A (diag) | «До ЕГЭ мало времени? Узнайте уровень за 30 мин бесплатно» | Записаться |
| VK Ads B (group) | «Группа ЕГЭ химия с 1 сент — 3 места, 1 500 ₽/чел» | Записаться |
| Direct | «Репетитор химия ЕГЭ онлайн — диагностика бесплатно» | /zapis |
| TG organic | E6 пост + кейсы учеников | himych.ru/zapis |
| SEO | Long-tail + «как выбрать репетитора» | CTA в статье |

### Tone

Экспертный, тёплый, без «лучший репетитор». Родителю — «вы». См. [brand-context](../brand-context.md).

---

## Channel Strategy

| Channel | Aug | Sep | Oct | Budget 3mo | Role |
|---------|-----|-----|-----|------------|------|
| **VK Ads** | 20k | 35k | 40k | **95k (70%)** | Primary acquisition |
| **Яндекс Direct** | — | 15k | 25k | **40k (30%)** | High-intent search pilot |
| **SEO / blog** | setup | 2 articles | 2 articles | time | Organic leads 4→6/mo |
| **Telegram** | 3 posts | weekly | weekly | time | Trust + E6 group |
| **Profi.ru** | update ad | maintain | maintain | ~6k commission | Baseline, not scale |
| **Referral** | — | soft launch | 2–4 payouts | ~7.5k | Word of mouth |

### VK Ads — август (E1 pilot)

| Setting | Value |
|---------|-------|
| Budget | 20 000 ₽ (~1 400 ₽/day, 15–31.08) |
| Objective | Leads / traffic → site |
| Audience | Родители, 35–55, интересы: ЕГЭ, репетитор, школа, 10–11 класс |
| Geo | РФ (или регион — уточнить) |
| Landing | `https://himych.ru/zapis?utm_source=vk&utm_medium=cpc&utm_campaign=aug2026_diag` |
| Creatives | 3 variants (A pain, B platform, C social proof) — см. [tilda-landing-vk-ads](../tilda-landing-vk-ads.md) |
| Gate E1 (31.08) | CPL ≤2 000 ₽, ≥2 probables → scale; иначе pause + CRO 2 weeks |

**Preconditions (blockers):**
- [ ] himych.ru + HTTPS live (**15.08**)
- [ ] Форма → Sheet работает
- [ ] CRO quick wins ([audit](../cro/zapis-analysis.md)): minimal header, no TG under hero form
- [ ] SEO technical: robots, sitemap, noindex app ([audit](../seo/audits/himych-audit-2026-07-29.md))
- [ ] 3+ organic VK posts before ads

### VK Ads — сентябрь–октябрь

- Scale **winning creative** from E1 (+20–30% budget if CPL ok)
- Add **retarget** (VK pixel / site visitors 30d)
- Campaign B: `/gruppa-ege` if E6 group not full by 25.08
- UTM: `utm_campaign=sep2026_diag`, `oct2026_diag`

### Яндекс Direct — с сентября

| Setting | Value |
|---------|-------|
| Pilot budget | 15k sen → 25k oct |
| Type | **Search only** (no РСЯ на старте) |
| Keywords (max 5–7) | репетитор химия егэ, репетитор по химии онлайн, подготовка егэ химия репетитор |
| Landing | /zapis (message match) |
| Minus-words | бесплатно курс, ответы, реферат, вакансия |
| Gate (30.09) | CAC ≤25k → continue; else off, VK+SEO only |

### Organic & Content

| Asset | Deadline | Owner |
|-------|----------|-------|
| E6 group post TG/VK | 5–11.08 | Роман |
| E2 bundle pitch (5 parents) | week 1 aug | Роман |
| `/repetitor-himiya-ege` | 31.08 | dev |
| Blog: «как выбрать репетитора» | 15.09 | Роман + `mkt-workflow-content-blog` |
| Blog: «задача 28 ЕГЭ» | 30.09 | Роман |
| FAQ schema on /zapis | 12.08 | dev |

---

## Content & Asset Checklist

### Must-have before VK launch (15.08)

| Asset | Format | Spec |
|-------|--------|------|
| Landing A `/zapis` | Next.js page | [tilda spec](../tilda-landing-vk-ads.md) + CRO fixes |
| Landing B `/gruppa-ege` | Next.js page | Group offer, 3 seats urgency |
| VK creative ×3 | 1080×1080, 1080×1920 | Photo + headline + CTA |
| Lead tracker | Google Sheet | [template](../leads-tracker-template.csv) |
| UTM convention | — | [brand-context](../brand-context.md) |
| Response SLA script | Text | «Перезвоним за 2ч…» |

### Nice-to-have (авг–сен)

| Asset | Skill |
|-------|-------|
| Hero photo | CRO audit |
| Platform screenshot block | CRO + landing |
| Welcome TG after form | `mkt-workflow-sequence-welcome` |
| `/ceny` page | SEO audit P0 |
| OG image | SEO |

### Creative brief (VK A — pain)

```
Visual: фото преподавателя, светлый фон
Headline: Химия на ЕГЭ — слабое место? Разберём за 30 мин бесплатно
Body: Онлайн · программа на год · платформа с ДЗ · без обязательств
CTA: Записаться на диагностику
URL: himych.ru/zapis?utm_...
```

→ Full briefs: `mkt-workflow-campaign-brief`  
→ Copy variants: `mkt-workflow-content-ads`

---

## Budget Allocation (Base)

| Month | VK | Direct | Other | **Total cash** |
|-------|-----|--------|-------|----------------|
| Август | 20 000 | 0 | ~2 000 (VPS) | **~22 000** |
| Сентябрь | 35 000 | 15 000 | ~2 000 | **~52 000** |
| Октябрь | 40 000 | 25 000 | ~2 500 | **~67 500** |
| **3 months** | **95 000** | **40 000** | **~18 000** | **~153 000** |

**Cap rule:** не превышать Base без gate 31.10. Агрессивный сценарий (200k ads) — только при E1+E2 green.

---

## Timeline & Milestones

### Phase 0: Prep (29.07 – 14.08)

| Date | Milestone | Deliverable |
|------|-----------|-------------|
| 05.08 | Slice 0 | VPS, `/zapis`, form → Sheet |
| 11.08 | E6 publish | Group post TG/VK |
| 12.08 | Slice 1 | `/gruppa-ege`, `/ceny`, robots+sitemap |
| 14.08 | CRO+SEO fixes | Minimal header, noindex app, FAQ schema |
| 15.08 | **Slice 2 GO** | himych.ru HTTPS → **VK ON** |

### Phase 1: VK Pilot (15.08 – 31.08)

| Week | Marketing | Ads | KPI check |
|------|-----------|-----|-----------|
| 15–21.08 | Daily CRM, answer <2h | 7k spend | CPL trend |
| 22–28.08 | A/B note best creative | 7k spend | CR landing |
| 29–31.08 | Retro E1 | 6k spend | **Gate 31.08** |

**August targets:** 21 leads, ~3 paid, CPL VK ~1 200 ₽

### Phase 2: Peak Season (01.09 – 30.09)

| Week | Focus |
|------|-------|
| 1–2 | Scale VK winner; 2 SEO articles live |
| 3 | Direct pilot 15k; retarget VK |
| 4 | **Gate 30.09** — Direct CAC |

**September targets:** 33 leads, ~5 paid

### Phase 3: Optimize (01.10 – 31.10)

| Week | Focus |
|------|-------|
| 1–2 | VK 40k + Direct 25k; cut loser ad sets |
| 3 | Monthly metrics retro; custdev ×3 |
| 4 | **Gate 31.10** — Q4 budget decision |

**October targets:** 44 leads, ~6 paid

---

## Content Calendar (high level)

| Week | Organic | Paid | SEO |
|------|---------|------|-----|
| W1 aug | E6 group post | — | — |
| W2 aug | VK cross-post ×2 | — | — |
| W3 aug | Creative prep | — | technical SEO |
| W4 aug | — | **VK 20k start** | — |
| W1 sep | TG weekly | VK scale | Article #1 publish |
| W2 sep | Referral soft | VK + retarget | Article #2 |
| W3 sep | — | + Direct 15k | — |
| W4 sep | Group fill push | optimize | — |
| Oct | TG weekly | VK+Direct | 2 articles |
| Nov plan | — | decision gate | — |

Detailed calendar: `mkt-workflow-campaign-calendar`

---

## Success Metrics & Tracking

### Primary KPIs

| Metric | Aug | Sep | Oct | Source |
|--------|-----|-----|-----|--------|
| Leads (total) | 21 | 33 | 44 | Sheet + API |
| CPL VK | ≤1 500 | ≤1 500 | ≤1 400 | VK Ads cabinet |
| CPL Direct | — | ≤3 000 | ≤2 800 | Direct |
| Lead → paid % | 14% | 16% | 14% | Sheet manual |
| New paid students | 3 | 5 | 6 | CRM |
| Marketing spend | 22k | 52k | 67k | Finance |
| CAC (ads only) | — | — | **≤13k** | calc |

### Secondary KPIs

| Metric | Target | Tool |
|--------|--------|------|
| Response time | <2h (goal <15min) | Sheet timestamp |
| Landing CR | 8–12% | ⚠️ Metrika `form_submit` |
| % non-Profi leads | 25→45% | Sheet source field |
| Group seats filled | ≥4 by 25.08 | Manual |
| E2 bundle yes | ≥2/5 | Experiment log |

### Attribution

```
utm_source=vk|yandex|google|telegram|profi
utm_medium=cpc|organic|social
utm_campaign=aug2026_diag|aug2026_group|sep2026_diag|...
utm_content=creative_a|creative_b|creative_c
```

**Rules:** не выдумывать цифры; без Метрики — manual weekly from Sheet + ad cabinets.

---

## Risk Mitigation

| Risk | P | Impact | Mitigation |
|------|---|--------|------------|
| Domain not ready 15.08 | Med | Ads delay | Staging only until HTTPS |
| CPL VK >3k | Med | Budget waste | Pause, CRO 2wk, lead form VK |
| Lead→paid <10% | Med | High CAC | <15min response, trial script |
| Landing 404 (/ceny, /blog) | High | Trust/SEO | Fix nav or remove links |
| App indexed | Med | Privacy/SEO | robots + noindex |
| Direct burns budget | Med | Cap 15k, search only |
| Burnout solo | High | Miss SLA | Cap 135k, no aggressive scenario |
| Sheet/form break | Low | Lost leads | Backend log + TG fallback |

---

## Dependencies & Blockers

```
Slice 0 (zapis) ──→ Slice 1 (gruppa, ceny) ──→ Slice 2 (domain) ──→ VK Ads
        │                                              │
        └── CRO fixes ─────────────────────────────────┘
        └── SEO robots/sitemap ────────────────────────┘
```

**Hard gate:** VK Ads **only after** `himych.ru/zapis` on HTTPS (not IP).

---

## Decision Gates

| Date | Question | Go | No-go |
|------|----------|-----|-------|
| **31.08** | E1 VK pilot | CPL ≤2k, ≥2 probables | Pause ads 2wk, fix landing |
| **30.09** | Direct pilot | CAC ≤25k | Direct off |
| **31.10** | Q4 scale | ≥5 organic+paid leads/mo | Hold 50k/mo ads |
| **31.10** | Teacher hire (Path C) | Sustainable pipeline | Delay |

---

## Agent / Skill Handoff

| Next step | Skill / persona |
|-----------|-----------------|
| Creative briefs | `mkt-workflow-campaign-brief` |
| VK ad copy ×3 | `mkt-workflow-content-ads` + `mkt-copywriter` |
| Weekly schedule | `mkt-workflow-campaign-calendar` |
| Landing CRO | `mkt-workflow-cro-form` |
| SEO technical | dev + [SEO audit](../seo/audits/himych-audit-2026-07-29.md) |
| Week 2/4 analyze | `mkt-workflow-campaign-analyze` |
| Monthly report | `mkt-workflow-report-monthly` |

---

## Immediate Actions (this week)

1. **Завершить Slice 0** — `/zapis` + Sheet (если не done)
2. **E6 пост** — набор группы 1 сентября (5–11.08)
3. **CRO quick wins** — minimal header, hero form без TG links
4. **SEO day-1** — robots.ts, sitemap.ts, metadataBase, noindex app
5. **Подготовить 3 VK креатива** — `mkt-workflow-content-ads`
6. **CRM Sheet** — колонки: source, utm, timestamp, status, paid Y/N

---

## Unresolved Questions

1. **Гео VK:** вся РФ или конкретный регион/город?
2. **himych.ru live date:** подтвердить до 10.08
3. **Фото для креативов:** есть готовое?
4. **Profi.ru:** обновить ссылку на himych.ru вместо taplink?
5. **E2 bundle:** результат опроса 5 родителей — влияет на ad copy «+500 отчёт»
