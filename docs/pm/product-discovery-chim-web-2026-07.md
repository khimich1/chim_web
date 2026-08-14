# Product Discovery (pm-product-discovery): chim_web / Химыч

**Дата:** 29.07.2026  
**Workflow:** `pm-workflow-discover` + OST + assumption prioritization + experiments  
**Product Stage:** **Existing product** — MVP построен (Phase 0–17), бизнес в фазе GTM  
**Discovery Question:** Как масштабировать репетиторский бизнес по химии (solo → учителя → школа), если главная боль — **привлечение учеников**?

**Контекст из диалога:**
- 8 лет онлайн-химия, 2 года группы; лиды: Профi.ру + сарафан
- Активы: chim_web, презентации на год, учебник, 1680+ заданий
- Три пути: (1) solo + app (2) нанять учителей (3) онлайн-школа
- План: VK/TG/MAX, реклама с 15 авг, бот — позже
- Strategy Canvas: [`strategy-chim-web-2026-07.md`](./strategy-chim-web-2026-07.md)

---

## Step 1. Discovery Context

| Параметр | Значение |
|----------|----------|
| **Продукт** | chim_web — платформа репетитора (ЕГЭ/ОГЭ): учебник, Stepik-тесты, ДЗ, AI, multi-teacher |
| **Бизнес-модель** | Занятия offline/online; app усиливает LTV, не продаётся отдельно (пока) |
| **Цены** | Инд. 2 500 ₽/ч; группа 1 500 ₽/чел × 2 ч |
| **Решения discovery** | Какой путь масштаба; когда реклама/бот/учителя; что валидировать первым |
| **Не discovery** | «Строить ли MVP» — уже построен |

---

## Step 2. Opportunity Solution Tree (OST)

### Desired Outcome (North Star discovery)

> **Увеличить Active Paying Students (APS)** — платящие ученики с активностью в app ≥1 раз / 14 дней  
> **Proxy на Q3 2026:** ≥8 заявок/мес, ≥40% из non-Профi.ру каналов

### Opportunities (customer perspective)

| ID | Opportunity (проблема клиента) | Importance | Satisfaction | Score* | Priority |
|----|--------------------------------|------------|--------------|--------|----------|
| O1 | «Не знаю, как найти **хорошего** репетитора по химии» | 9 | 4 | **5.4** | **P0** |
| O2 | «Не вижу, **что ребёнок делает** между занятиями» | 8 | 3 | **5.6** | **P0** |
| O3 | «Ребёнок **бросает** после 2–3 занятий / не делает ДЗ» | 8 | 4 | **4.8** | **P1** |
| O4 | «**Органика и расчёты** (27–34) — слабое место» | 9 | 5 | **4.5** | **P1** |
| O5 | «**Дорого** / непонятно за что плачу vs Умскул» | 7 | 5 | **3.5** | P2 |
| O6 | «Нужен **график группы**, а не только индивидуал» | 7 | 6 | **2.8** | P2 |

*Score ≈ Importance × (1 − Satisfaction/10) — qualitative

### Solutions mapped to opportunities

#### O1 — Найти репетитора (GTM)

| Solution | Описание | Effort |
|----------|----------|--------|
| S1.1 | SEO-сайт + long-tail статьи | Medium |
| S1.2 | VK/TG контент + VK Ads (авг) | Low–Med |
| S1.3 | Реферальная программа | Low |
| S1.4 | Профi.ру optimization | Low |
| S1.5 | Яндекс Директ (пилот Q3) | Med |

**Focus Q3:** S1.2 + S1.4 + S1.1 (MVP landing)

#### O2 — Прозрачность прогресса

| Solution | Описание | Effort |
|----------|----------|--------|
| S2.1 | Все ученики в chim_web + weekly ДЗ | Low |
| S2.2 | Bundle «занятия + платформа» | Low |
| S2.3 | Ручной отчёт родителю (1 msg/2 нед) | Low |
| S2.4 | Кабинет родителя | High |

**Focus Q3:** S2.1 + S2.2 + S2.3

#### O3 — Engagement / retention

| Solution | Описание | Effort |
|----------|----------|--------|
| S3.1 | Welcome-онбординг (✅ есть) | Done |
| S3.2 | Streak + рейтинг (✅ есть) | Done |
| S3.3 | Magic link вход | Med |
| S3.4 | Обязательное ДЗ после занятия | Low |

**Focus Q3:** S3.4 + метрики WAU

#### O4 — Слабые темы

| Solution | Effort |
|----------|--------|
| S4.1 Учебник + Stepik (✅) | Done |
| S4.2 AI-советчик по учебнику (✅) | Done |
| S4.3 TG-разборы задач 27–34 | Low |

#### Scale paths (из диалога) — solutions на бизнес-уровне

| Path | Связанные opportunities | Когда |
|------|-------------------------|-------|
| **Path A:** Solo + app | O2, O3, O4 | **Сейчас** |
| **Path B:** Multi-channel GTM | O1, O5 | **Q3–Q4 2026** |
| **Path C:** Сеть учителей | O1 (capacity), O6 | **12+ мес** |
| **Path D:** Онлайн-школа | O1, O5, O6 | **18+ мес** |

---

## Step 3. Brainstorm (Product Trio) — 15 идей → Top 5

### Product Manager (5)

| # | Idea | Rationale |
|---|------|-----------|
| PM1 | Bundle «занятия + платформа + отчёты» | Прямой ответ O2, premium pricing |
| PM2 | Набор группы сент/янв как product | O6, выше ₽/час |
| PM3 | VK Ads → диагностика (авг пилот) | O1, быстрый тест GTM |
| PM4 | Реферальная программа | Lowest CAC |
| PM5 | SEO lead magnet «5 задач типа 28» | O1 + O4, compound |

### Product Designer (5)

| # | Idea | Rationale |
|---|------|-----------|
| D1 | «Первое ДЗ за 24ч» после пробного | O3 activation |
| D2 | Родительский one-pager «что видно в app» | O2, sales aid |
| D3 | Landing с 3 отзывами + видео 60 сек | O1 conversion |
| D4 | TG-закреп + единый оффер везде | Consistency |
| D5 | WhatsApp/TG авто-напоминание о ДЗ | O3 (manual first) |

### Engineer (5)

| # | Idea | Rationale |
|---|------|-----------|
| E1 | UTM + таблица лидов (Sheets) | Measure channels |
| E2 | Tilda landing за 5 дней | Unblock ads |
| E3 | WAU/ДЗ dashboard для teacher | O2 data |
| E4 | Content queue bot + **approve** (Q4) | Scale posting, not blind AI |
| E5 | Public mini-test API (5 вопросов) | Lead magnet → app |

### Top 5 (selected for stress-test)

| Rank | Idea | Opportunities | Why top |
|------|------|---------------|---------|
| **1** | **VK/TG прогрев + VK Ads 15 авг** | O1 | Сезон набора; быстрый learning |
| **2** | **Solo + app + bundle pitch** | O2, O3 | Zero risk, immediate LTV |
| **3** | **Групповой набор (productized)** | O6, O1 | Уже 2 года опыта |
| **4** | **SEO + lead magnet** | O1, O4 | Compound moat |
| **5** | **Реферальная программа** | O1 | Cheap, trust-based |

**Deferred:** бот автопостинг (E4), найм учителей (Path C), кабинет родителя (S2.4)

---

## Step 4. Assumptions (master list)

### Path A — Solo + platform

| ID | Assumption | Category | Confidence |
|----|------------|----------|------------|
| A-V1 | Родители ценят видимость прогресса в app | Value | Medium |
| A-V2 | Bundle +500–1000 ₽/мес приемлем | Value | Low |
| A-U1 | Ученики войдут и сделают 1-е ДЗ без magic link | Usability | Medium |
| A-B1 | WAU ≥50% → retention +1–2 мес | Value | Medium |

### Path B — GTM (VK/TG/SEO/ads)

| ID | Assumption | Category | Confidence |
|----|------------|----------|------------|
| B-G1 | VK Ads CPL <4 000 ₽ при прогретом VK | GTM | Low |
| B-G2 | ≥3 поста до рекламы снижают CPL | GTM | Medium |
| B-G3 | SEO: 15 статей → ≥2 leads/mo | GTM | Low |
| B-G4 | Taplink достаточен до Tilda (авг) | Feasibility | High |
| B-G5 | Конверсия заявка→пробное ≥30% | GTM | Medium |

### Path C — Учителя (future)

| ID | Assumption | Category | Confidence |
|----|------------|----------|------------|
| C-V1 | Учитель по слайдам ≥80% вашего качества | Value | Low |
| C-G1 | ≥5 leads/mo с вашего маркетинга до найма | GTM | Low |
| C-B1 | Маржа 30–35% окупает ops | Viability | Medium |

### Path D — Школа (future)

| ID | Assumption | Category | Confidence |
|----|------------|----------|------------|
| D-V1 | Бренд школы не cannibalize premium 1:1 | Viability | Medium |
| D-B1 | 3–5 учителей управляемы solo-founder | Feasibility | Low |

### Cross-cutting

| ID | Assumption | Category | Confidence |
|----|------------|----------|------------|
| X-T1 | Solo: 70% teach / 20% market / 10% dev sustainable | Team | Medium |
| X-T2 | Профi.ru не даст >3 leads/mo без роста spend | GTM | High |

---

## Step 5. Assumption Prioritization (Impact × Risk)

| ID | Assumption | Impact | Risk | Quadrant | Action |
|----|------------|--------|------|----------|--------|
| **B-G1** | VK Ads CPL <4k | Critical | High | **Test** | Exp E1 |
| **B-G2** | Прогрев снижает CPL | High | Med | **Test** | Exp E1 |
| **A-V2** | Bundle pricing works | High | High | **Test** | Exp E2 |
| **A-B1** | WAU → retention | High | Med | **Test** | Exp E3 |
| **B-G3** | SEO 15 articles → leads | Critical | High | **Test** | Exp E4 |
| **C-V1** | Teacher quality | Critical | High | Defer | Exp E7 (Q1 2027) |
| **C-G1** | Leads before hire | Critical | High | Defer | Gate metric |
| B-G5 | Conversion заявка→пробное | High | Med | Proceed | Process fix |
| B-G4 | Taplink OK for Aug | Med | Low | **Proceed** | Ship |
| X-T2 | Profi ceiling | Med | Low | **Proceed** | Audit E5 |
| A-V1 | Parents value progress | High | Med | Proceed | Bundle + reports |
| E4 bot | Autopost saves time | Low | Med | **Defer** | Q4 |

**Leap of faith (P0):** B-G1, B-G3, A-V2, A-B1

---

## Step 6. Experiments

### E1 — VK Ads pilot (B-G1, B-G2)

| Field | Detail |
|-------|--------|
| **Hypothesis** | При 3+ organic posts и budget 20k/2 нед CPL ≤4k и ≥2 probables |
| **Method** | 29 Jul–14 Aug: 3 posts TG+VK; 15 Aug: VK Ads 1400₽/day, geo parents 35–55 |
| **Metric** | CPL, заявки, probables, paid conversions |
| **Success** | ≥2 probables, CPL ≤4k, ≥1 paid |
| **Fail** | 0 probables at ≥8 leads → fix offer/sales, not budget |
| **Effort** | 8h setup + daily 15min |
| **Timeline** | 15 Aug – 31 Aug |

### E2 — Bundle pitch (A-V2)

| Field | Detail |
|-------|--------|
| **Hypothesis** | ≥2/5 parents accept +500₽/mo for «platform + reports» |
| **Method** | Personal message/call to 5 current parents |
| **Metric** | Yes/No/Negotiate |
| **Success** | ≥2 yes |
| **Fail** | 0 yes → include platform free, use as differentiator in ads |
| **Effort** | 2h |
| **Timeline** | Week 1 Aug |

### E3 — Engagement → retention proxy (A-B1)

| Field | Detail |
|-------|--------|
| **Hypothesis** | Students with ≥2 HW/week have higher 3-mo retention |
| **Method** | Track WAU, HW/week for all students in app 4 weeks |
| **Metric** | WAU%, HW/week, correlate with tenure |
| **Success** | WAU ≥50%, avg ≥2 HW/week |
| **Fail** | WAU <30% → mandatory HW policy + onboarding fix |
| **Effort** | 1h/week review |
| **Timeline** | Aug–Sep |

### E4 — SEO smoke test (B-G3)

| Field | Detail |
|-------|--------|
| **Hypothesis** | 5 articles + landing → ≥2 leads in 8 weeks |
| **Method** | Publish 5 long-tail from playbook; CTA diagnostic |
| **Metric** | Organic visits, form submits |
| **Success** | ≥2 leads |
| **Fail** | 0 leads → review geo/keywords; add Telegram |
| **Effort** | 6h/article × 5 |
| **Timeline** | Aug–Oct |

### E5 — Profi.ru ceiling audit (X-T2)

| Field | Detail |
|-------|--------|
| **Hypothesis** | Profi provides ≤X leads/mo at Y% commission |
| **Method** | Export 6mo data: views, chats, bookings, revenue, commission |
| **Success** | Clear ceiling number for planning |
| **Effort** | 3h |
| **Timeline** | Week 1 |

### E6 — Group enrollment (PM2)

| Field | Detail |
|-------|--------|
| **Hypothesis** | «Group Sep 1» post fills 4+ seats from TG+Profi+referral |
| **Method** | Single CTA post all channels 15 Aug |
| **Success** | ≥4 paid seats |
| **Timeline** | Aug |

### E7 — Teacher quality (C-V1) — DEFER

| Field | Detail |
|-------|--------|
| **When** | Q1 2027 if ≥5 non-Profi leads/mo |
| **Method** | 1 colleague, 2 probables, NPS survey |

### E8 — Content bot (E4) — DEFER Q4

| Field | Detail |
|-------|--------|
| **Hypothesis** | Approve-flow bot saves ≥2h/mo vs manual |
| **Precondition** | 8+ manual posts without miss |

---

## Step 7. Discovery Plan & Timeline

```
Week 1 (29 Jul–4 Aug)
  E5 Profi audit | E2 bundle pitch | TG/VK закреп + post 1 | All students in app

Week 2–3 (5–18 Aug)
  E3 start WAU tracking | Posts 2–3 | Tilda/Taplink ready | E6 group CTA prep

Week 3–4 (15–31 Aug)
  E1 VK Ads pilot | Daily lead log with UTM

Sep–Oct
  E4 SEO 5 articles | E3 continue | Referral launch | Retros E1

Nov
  Decision: scale VK / add Direct / SEO double-down

Q1 2027
  Gate: if ≥5 non-Profi leads/mo → plan E7 teacher pilot
```

### Decision Framework

| Result | Decision |
|--------|----------|
| E1 success | Scale VK to 2k/day Sep; add Direct 15k |
| E1 fail | Fix landing/offer; SEO+referral focus |
| E2 success | Bundle in price list for all new |
| E2 fail | Free platform in marketing copy |
| E3 fail | Mandatory HW + parent report template |
| E4 fail at 8 weeks | Custdev 5 parents; revise keywords |
| Oct: ≥40% non-Profi leads | Green light to **plan** teacher Q1 |
| Oct: still >60% Profi | Delay Path C; intensify owned channels |

---

## Step 8. Metrics Dashboard (discovery phase)

| Metric | Source | Frequency | Q3 Target |
|--------|--------|-----------|-----------|
| Leads total | Sheets CRM | Weekly | 8–12/mo |
| Leads by channel | UTM + ask | Weekly | 4+ channels active |
| % non-Profi | Calc | Monthly | ≥40% by Oct |
| CPL VK | Ads cabinet | Weekly | ≤4k |
| Application→trial | CRM | Weekly | ≥30% |
| Trial→paid | CRM | Monthly | ≥25% |
| WAU students | app activity | Weekly | ≥50% |
| HW/week/student | app | Weekly | ≥2 |
| APS | paid + active | Monthly | +3–5 new/mo |
| NPS parent | survey | Quarterly | ≥8 |

**Tooling now:** Google Sheets (see [telegram playbook §8](../marketing/telegram-channel-playbook.md)).  
**Later:** `pm-workflow-setup-metrics` → North Star dashboard PRD.

---

## Step 9. Devil's Advocate Summary

| Perspective | Top failure mode |
|-------------|------------------|
| **PM** | Aug ads before trust assets → burn 20k with 0 conversions |
| **Designer** | App complexity → students don't login → bundle unsellable |
| **Engineer** | Build bot before posts → 2 weeks lost, 0 leads |
| **Mitigation** | 3 posts before ads; E2/E3 parallel; bot deferred |

---

## Artifacts Index

| Document | Role |
|----------|------|
| [strategy-chim-web-2026-07.md](./strategy-chim-web-2026-07.md) | Strategy Canvas |
| [discovery-chim-web-2026-07.md](./discovery-chim-web-2026-07.md) | First discover (monetization focus) |
| [telegram-channel-playbook.md](../marketing/telegram-channel-playbook.md) | TG execution |
| [seo-strategy.md](../strategy/seo-strategy.md) | SEO IA |
| [custdev-interview-script.md](../research/custdev-interview-script.md) | Parent interviews |

---

## Next Steps (pm-product-discovery commands)

- [x] **`pm-workflow-interview prep`** → [`custdev-gtm-parents-2026-07.md`](./custdev-gtm-parents-2026-07.md)  
- [x] **`pm-workflow-setup-metrics`** → [`metrics-dashboard-chim-web-2026-07.md`](./metrics-dashboard-chim-web-2026-07.md)  
- [x] **E1 + E6 materials** → [`experiments-aug-2026.md`](../marketing/experiments-aug-2026.md)  
- [x] **CRM template** → [`leads-tracker-template.csv`](../marketing/leads-tracker-template.csv)  
- [ ] Execute **E1–E6** in August (checklist in experiments doc)  
- [ ] **`pm-workflow-brainstorm experiments`** — E7 teacher pilot (Q1 2027)  
- [ ] 3 custdev interviews → update assumptions table below  

---

## Checkpoint

**Решение по умолчанию (если без корректировки):**  
**29 Jul–14 Aug** — organic (3 posts) → **15 Aug** — VK Ads E1.

**Top 5 in execution:** E2 bundle → E6 group post → E1 VK Ads → E3 WAU → E4 SEO.
