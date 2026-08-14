# Metrics Dashboard: chim_web / Химыч

**Дата:** 29.07.2026  
**Workflow:** `pm-workflow-setup-metrics`  
**Stage:** Growth / discovery (Q3 2026)  
**Связано:** [product-discovery](./product-discovery-chim-web-2026-07.md), [strategy](./strategy-chim-web-2026-07.md)

---

## 1. North Star Metric

### Active Paying Students (APS)

**Формула:**
```
APS = count(students WHERE paid_lesson_in_last_30d = true
            AND app_activity_in_last_14d = true)
```

**App activity** = хотя бы одно: login, submit HW, complete test step, textbook chunk read.

**Почему NSM:** объединяет revenue (занятия) и product value (работа между уроками). Рост APS без activity = «платят, но app мёртв» — не цель.

| Критерий | ✓ |
|----------|---|
| Measures value delivery | Да — ученик учится, не только сидит на уроке |
| Leading indicator | Да — activity → retention → referrals |
| Actionable | Да — ДЗ, онбординг, bundle влияют напрямую |

**Q3 2026 target:** +3–5 новых APS/мес, total APS growth ≥15% к 31.10.

---

## 2. Input Metrics (drivers)

```
Leads → Trial → Paid → Active in app → Retained → Referral
  │        │       │         │              │          │
  GTM    Sales  Revenue   Product       LTV         CAC↓
```

| # | Metric | Formula | Owner | Q3 Target | Source |
|---|--------|---------|-------|-----------|--------|
| I1 | **Leads / month** | Count form/TG/Profi inquiries | Marketing | 8–12 | CRM Sheet |
| I2 | **% non-Profi leads** | (leads − profi) / total | Marketing | ≥40% by Oct | CRM |
| I3 | **Lead → trial ≤7d** | trials / leads (7d window) | Sales | ≥30% | CRM |
| I4 | **Trial → paid** | first_payment / trials | Sales | ≥25% | CRM |
| I5 | **WAU / APS** | weekly_active / APS | Product | ≥50% | app activity |
| I6 | **HW per student / week** | avg submitted HW | Product | ≥2 | app |
| I7 | **Referral leads / month** | leads source=referral | Marketing | ≥1 | CRM |

---

## 3. Health Metrics (guardrails)

| Metric | Green | Yellow | Red | Frequency |
|--------|-------|--------|-----|-----------|
| Response time to lead | <2h | 2–8h | >8h | Per lead |
| Parent NPS | ≥8 | 6–7 | <6 | Quarterly |
| Student churn <1 mo | <15% | 15–25% | >25% | Monthly |
| Students 0 activity 14d | <30% | 30–50% | >50% | Weekly |
| VK Ads CPL | <4k | 4–6k | >6k | Weekly (campaign) |
| AI complaint / parent concern | 0 | 1 | ≥2 | Monthly |

---

## 4. Counter-Metrics

| NSM optimization | Counter-metric | Why |
|------------------|----------------|-----|
| Push WAU up | % HW copied without understanding | Empty engagement |
| More leads (ads) | Trial→paid conversion | Junk leads |
| Mandatory HW | Student NPS / complaints | Burnout |

---

## 5. Alert Thresholds

| Metric | Green | Yellow → action | Red → action |
|--------|-------|-----------------|--------------|
| Leads/week | ≥2 | 1 → review channels | 0 for 2 weeks → emergency content + Profi boost |
| CPL VK | ≤4k | 4–6k → change creative | >6k for 5 days → pause campaign |
| WAU% | ≥50% | 30–50% → HW policy | <30% → onboarding fix |
| Trial→paid | ≥25% | 15–25% → review diagnostic script | <15% → custdev 3 parents |

---

## 6. Dashboard Layout (weekly review — 15 min)

### Row 1: Business
- APS (total)
- New paid this month
- Revenue estimate (hours × rate)

### Row 2: Funnel
- Leads by channel (stacked)
- Lead→trial→paid (conversion %)

### Row 3: Product
- WAU %
- HW/week avg
- Students inactive 14d (list names → action)

### Row 4: Marketing (if ads on)
- Spend / leads / CPL
- Creative A vs B

---

## 7. CRM Sheet Schema

**File:** `docs/marketing/leads-tracker-template.csv` (copy to Google Sheets)

| Column | Example |
|--------|---------|
| date | 2026-08-15 |
| name | Иванова |
| contact | @telegram / +7… |
| class | 11 |
| exam | EGE |
| source | vk_ads / telegram / profi / referral / seo |
| utm_campaign | aug2026_group |
| trial_date | 2026-08-17 |
| paid | yes/no |
| bundle | yes/no/+500 |
| notes | «искала органику» |

**Weekly formula cells:**
- Leads MTD: `=COUNTIF(A:A,">="&DATE(...))`
- Conversion: trials/leads
- By source: pivot table

---

## 8. App Metrics (manual until analytics PRD)

Пока нет product analytics — **teacher dashboard + weekly export**:

| Event | How to track now |
|-------|------------------|
| Login | `activity` table / teacher stats |
| HW submit | homework submissions count |
| Test steps | test session progress |
| Streak | leaderboard API |

**E3 experiment (Aug–Sep):** каждый понедельник — выписать WAU и HW/week per student в Sheet.

---

## 9. OKR Q3 2026 (from metrics)

| Objective | Key Result | Metric |
|-----------|------------|--------|
| O1: Снизить зависимость от Профi.ру | KR1: ≥40% leads non-Profi | I2 |
| O1 | KR2: ≥8 leads/mo avg | I1 |
| O2: Доказать value app | KR1: WAU ≥50% | I5 |
| O2 | KR2: ≥2 HW/week | I6 |
| O3: Валидировать paid GTM | KR1: VK CPL ≤4k | CPL |
| O3 | KR2: ≥2 paid from VK pilot | CRM |

---

## 10. Tooling Roadmap

| Phase | Tool | When |
|-------|------|------|
| Now | Google Sheets CRM | Aug 2026 |
| Now | Yandex Metrika on landing | Aug 2026 |
| Q4 | Metrika goals + UTM auto | Oct 2026 |
| 2027 | Parent dashboard | PRD |
| 2027 | Automated APS in admin | Feature |

---

## 11. Review Cadence

| Ritual | When | Duration |
|--------|------|----------|
| Lead log update | Daily (if ads) | 5 min |
| Weekly metrics | Mon 9:00 | 15 min |
| Monthly strategy check | 1st Mon | 30 min |
| Post-campaign retro | After E1 | 45 min |
