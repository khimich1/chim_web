# SEO Audit: himych.ru (chim_web marketing)

**Дата:** 29.07.2026  
**Scope:** Recommended (Technical + On-Page + Content + roadmap)  
**Skills:** `mkt-workflow-seo-audit`, `mkt-seo-mastery`  
**Target:** `frontend/app/(marketing)/` → prod `himych.ru`

## Configuration

| Parameter | Value |
|-----------|-------|
| Focus | Technical, On-Page, Content Quality |
| Baseline | ⚠️ No baseline — site pre-launch / no GSC |
| Priority | Impact/Effort matrix |
| Indexable pages (code) | 4: `/`, `/zapis`, `/privacy` + app routes at risk |

---

## Health Score: **38/100**

| Category | Score | Weight | Notes |
|----------|-------|--------|-------|
| Technical SEO | 25/100 | 30% | No robots, sitemap, noindex on app |
| On-Page SEO | 55/100 | 25% | `/zapis` ok; missing pages, schema |
| Content | 15/100 | 30% | 3 marketing pages vs 20+ in plan |
| Off-Page / Authority | ⚠️ N/A | 15% | GSC/Semrush not connected |

**Verdict:** фундамент landing `/zapis` заложен, но **SEO-инфраструктура не готова к индексации**. App-роуты могут утекать в индекс. Контентная стратегия (keyword research) не реализована в коде.

---

## Data Sources

| Source | Status |
|--------|--------|
| Google Search Console | ⚠️ NOT AVAILABLE |
| Semrush / Wordstat | ⚠️ NOT AVAILABLE (estimates in docs only) |
| Code review | ✅ VERIFIED |
| Keyword map | 📊 FROM FILE — `docs/marketing/seo-keywords-research-2026-07.md` |
| SEO strategy | 📊 FROM FILE — `docs/strategy/seo-strategy.md` |
| PageSpeed / CWV | ⚠️ NOT AVAILABLE (run after deploy) |

---

## Executive Summary

**Сильные стороны:** русский `lang`, metadata на marketing-страницах, canonical tags, `/zapis` заточен под коммерческий интент «репетитор химия ЕГЭ», keyword research и IA уже описаны в docs.

**Критические пробелы:**
1. **Нет `robots.txt` и `sitemap.xml`**
2. **`/student/*`, `/teacher/*`, `/login` без `noindex`** — риск индексации app (стратегия требует обратного)
3. **Нет `metadataBase`** — абсолютные canonical/OG для Яндекса
4. **Broken IA:** header/home ссылаются на `/ceny`, `/blog` — страниц нет (404 → crawl waste)
5. **Нет schema.org** (FAQ, LocalBusiness, Person)
6. **Контент:** 0 статей из 15+ в keyword plan

---

## Critical Issues

| # | Issue | Severity | Pages | Fix |
|---|-------|----------|-------|-----|
| 1 | App routes indexable | 🔴 Critical | `/login`, `/student/*`, `/teacher/*` | `robots.txt` Disallow + `robots: noindex` в layout app |
| 2 | No robots.txt | 🔴 Critical | site-wide | `app/robots.ts` |
| 3 | No sitemap | 🔴 Critical | marketing | `app/sitemap.ts` — `/`, `/zapis`, `/privacy`, future pages |
| 4 | No metadataBase | 🔴 Critical | all | `metadataBase: https://himych.ru` in root layout |
| 5 | 404 from nav (`/ceny`, `/blog`) | 🔴 Critical | header, home | Create pages or remove links until ready |
| 6 | No JSON-LD schema | 🟠 High | `/zapis` | FAQPage + Person + Service |
| 7 | Content gap vs plan | 🟠 High | — | P0 pages: `/repetitor-himiya-ege`, `/ceny`, blog #1 |
| 8 | Root metadata leak | 🟡 Med | app fallback | `chim_web — химия` in root `layout.tsx` may apply to non-marketing routes |

---

## 1. Technical SEO

### 1.1 Crawlability

| Check | Status | Detail |
|-------|--------|--------|
| robots.txt | ❌ Missing | No `frontend/app/robots.ts` |
| sitemap.xml | ❌ Missing | No `frontend/app/sitemap.ts` |
| HTTPS | ⚠️ Assume ok on Timeweb VPS | Verify after deploy |
| Mobile-friendly | ✅ Responsive Tailwind | marketing pages |
| Broken internal links | ❌ `/ceny`, `/blog` in nav | 404 until created |

**Recommended `robots.txt`:**

```
User-agent: *
Allow: /
Disallow: /login
Disallow: /student/
Disallow: /teacher/
Disallow: /api/

Sitemap: https://himych.ru/sitemap.xml
```

### 1.2 Indexability

| Route | Current | Should be |
|-------|---------|-----------|
| `/` | index (default) | ✅ index |
| `/zapis` | index | ✅ index |
| `/privacy` | index | ✅ index (or noindex — optional) |
| `/login` | index ⚠️ | **noindex** |
| `/student/*` | index ⚠️ | **noindex** |
| `/teacher/*` | index ⚠️ | **noindex** |

**Risk:** Google/Яндекс могут проиндексировать `/login`, тексты UI кабинета — duplicate/thin + privacy leak per `seo-strategy.md`.

**Fix pattern (Next.js App Router):**

```typescript
// app/student/layout.tsx, app/teacher/layout.tsx, app/login/page.tsx
export const metadata: Metadata = {
  robots: { index: false, follow: false },
};
```

### 1.3 Canonical & metadataBase

Current `/zapis`:

```typescript
alternates: { canonical: "/zapis" }
```

Without `metadataBase`, crawlers get **relative** canonical — Яндекс предпочитает абсолютные URL.

**Fix:**

```typescript
// app/layout.tsx or (marketing)/layout.tsx
export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "https://himych.ru"),
  // ...
};
```

### 1.4 Core Web Vitals

⚠️ NOT AVAILABLE — run after deploy:
- [PageSpeed Insights](https://pagespeed.web.dev/) for `/` and `/zapis`
- Target: LCP <2.5s, CLS <0.1

**Code hints (likely good):**
- Next.js standalone, minimal JS on marketing (Server Components)
- No heavy hero images yet (fast but hurts trust — see CRO audit)
- `LeadForm` is client component — acceptable island

### 1.5 Structured Data

| Schema | Page | Status | Rich result |
|--------|------|--------|-------------|
| FAQPage | `/zapis` | ❌ | FAQ in SERP |
| Person | `/zapis`, `/o-prepodavatele` | ❌ | Knowledge panel lite |
| LocalBusiness / ProfessionalService | `/zapis` | ❌ | Local pack (online service) |
| Organization | `/` | ❌ | Brand |
| BreadcrumbList | blog (future) | ❌ | Navigation |

→ `mkt-workflow-seo-schema`

---

## 2. On-Page SEO

### 2.1 Page-by-Page Audit

#### `/` (home)

| Element | Current | Score | Recommendation |
|---------|---------|-------|----------------|
| Title | «Химыч — репетитор по химии ЕГЭ и ОГЭ онлайн» (~45 chars) | 🟢 | Good; add «бесплатная диагностика» if room |
| Meta desc | 89 chars | 🟡 | Expand to 140–160, CTA «Запишитесь» |
| H1 | «Химыч — подготовка к ЕГЭ и ОГЭ онлайн» | 🟡 | Add keyword «репетитор по химии» |
| Keyword in first 100 words | Partial | 🟡 | «репетитор по химии» in intro ✅ |
| Internal links | `/zapis`, `/ceny`❌, `/blog`❌ | 🔴 | Fix broken; link to `/zapis` with anchor text |
| Content depth | ~150 words | 🔴 | Thin — expand or merge with `/repetitor-himiya-ege` |
| OG | Default only | 🟡 | Add `openGraph.images` |

#### `/zapis` (primary money page)

| Element | Current | Score | Recommendation |
|---------|---------|-------|----------------|
| Title | «Репетитор по химии ЕГЭ — бесплатная диагностика \| Химыч» (~52 chars) | 🟢 | Strong commercial intent |
| Meta desc | ~95 chars | 🟡 | Extend: «30 мин бесплатно · онлайн по РФ · платформа с ДЗ» |
| H1 | «Репетитор по химии ЕГЭ и ОГЭ» + sub | 🟢 | Matches target queries |
| H2 structure | Social proof, features, pricing, FAQ | 🟢 | Logical |
| Keyword density | Natural | 🟢 | ЕГЭ, химия, диагностика, репетитор |
| Images / alt | No images | 🔴 | Add photo + platform screenshot with alt |
| FAQ | 5 questions | 🟢 | → FAQPage schema |
| Cannibalization vs `/` | Overlap | 🟡 | Differentiate: `/` = brand, `/zapis` = conversion, future `/repetitor-himiya-ege` = SEO hub |

#### `/privacy`

| Element | Score | Note |
|---------|-------|------|
| Title | 🟢 | ok |
| Index | 🟡 | `index: true` — ok for trust; low priority page |
| Content | 🟡 | Draft text — complete for 152-ФЗ before ads |

### 2.2 Missing Pages (from keyword map)

| Priority | URL | Target keyword | Status |
|----------|-----|----------------|--------|
| **P0** | `/repetitor-himiya-ege` | репетитор химия егэ | ❌ Missing |
| **P0** | `/ceny` | стоимость репетитора химия | ❌ Linked but 404 |
| **P0** | `/blog/kak-vybrat-repetitora-himiya-ege` | как выбрать репетитора | ❌ No blog |
| P1 | `/o-prepodavatele` | доверие | ❌ (about block only on /zapis) |
| P1 | `/otzyvy` | отзывы репетитор химия | ❌ (reviews on /zapis only) |
| P2 | `/blog/zadacha-28-ege-himiya` | задача 28 егэ химия | ❌ |

**Gap:** ~95% planned SEO IA not built.

### 2.3 Search Intent Mapping

| Intent | Query example | Best page today | Ideal page |
|--------|---------------|-----------------|------------|
| Transactional | репетитор химия егэ | `/zapis` 🟡 | `/repetitor-himiya-ege` → CTA `/zapis` |
| Commercial | сколько стоит репетитор химия | ❌ 404 `/ceny` | `/ceny` |
| Informational | как выбрать репетитора химия | ❌ | `/blog/...` |
| Informational | задача 28 егэ химия | ❌ | `/blog/...` |
| Navigational | химыч репетитор | `/` 🟢 | `/` |

---

## 3. Content Quality

### 3.1 Thin Content

| Page | Word count (est.) | Verdict |
|------|-------------------|---------|
| `/` | ~150 | 🔴 Thin — add sections or redirect to `/repetitor-himiya-ege` |
| `/zapis` | ~600+ | 🟢 Acceptable for landing |
| `/privacy` | ~80 | 🟡 Ok for legal stub |

### 3.2 Content Clusters (planned vs reality)

```
Pillar: /repetitor-himiya-ege     ❌ NOT BUILT
├── /blog/kak-vybrat-...          ❌
├── /blog/repetitor-ili-shkola    ❌
├── /blog/zadacha-28-...          ❌
└── /zapis (CTA)                  ✅
```

### 3.3 E-E-A-T (Experience, Expertise, Authority, Trust)

| Signal | Status |
|--------|--------|
| Author name | ✅ Роман Алексеевич on /zapis |
| Experience | ✅ «8 лет», «100+ учеников» |
| Photo | ❌ Missing |
| Credentials | ❌ No education/certs |
| Reviews | 🟡 Text only, no verification |
| Privacy policy | 🟡 Draft |
| Physical/online presence | 🟡 «онлайн по РФ» |

---

## 4. Off-Page & Competitive (limited)

⚠️ Backlink profile, DA, SERP positions — **NOT AVAILABLE** without GSC/Semrush.

### SERP context (from keyword research doc)

| Query type | Who ranks | Your angle |
|------------|-----------|------------|
| репетитор химия егэ | Profi, Avito, школы | Solo + platform + diagnostic |
| задача 28 егэ | 100points, Дзен, Stepenin | Repurposed from your teaching + mini-test |
| подготовка к егэ химии | Mel, Foxford, aggregators | Don't compete head-on; long-tail first |

**Strategy validated in docs:** СЧ commercial on landings + НЧ/микро by task numbers — **correct for solo site**.

---

## Quick Wins (Impact × Effort)

| # | Action | Impact | Effort | ETA |
|---|--------|--------|--------|-----|
| 1 | `robots.ts` + block app | 🔴 High | 30 min | Day 1 |
| 2 | `sitemap.ts` (3–5 URLs) | 🔴 High | 30 min | Day 1 |
| 3 | `metadataBase` + absolute canonical | 🔴 High | 15 min | Day 1 |
| 4 | `noindex` on login/student/teacher | 🔴 High | 30 min | Day 1 |
| 5 | Remove/fix `/ceny`, `/blog` links | 🟠 Med | 15 min | Day 1 |
| 6 | FAQ JSON-LD on `/zapis` | 🟠 Med | 1 h | Day 2 |
| 7 | Expand meta descriptions to 140–160 | 🟡 Med | 30 min | Day 2 |
| 8 | OG image (brand + headline) | 🟡 Med | 2 h | Week 1 |
| 9 | Яндекс.Метрика + Вебмастер | 🟠 Med | 1 h | Before index |
| 10 | Submit sitemap to Yandex + Google | 🟠 Med | 30 min | After deploy |

---

## High-Impact (Weeks 1–4)

### Week 1: Technical foundation
- [ ] robots.ts, sitemap.ts, metadataBase
- [ ] noindex app routes
- [ ] Fix nav 404s
- [ ] Register Yandex Webmaster + Google Search Console
- [ ] PageSpeed baseline on prod

### Week 2: Money pages
- [ ] `/repetitor-himiya-ege` — 800–1200 words, CTA → `/zapis`
- [ ] `/ceny` — transparent pricing (already on /zapis, dedupe carefully)
- [ ] Person + Service schema
- [ ] Internal linking: home → service → zapis

### Week 3–4: Content P0 (from keyword research)
- [ ] `/blog/kak-vybrat-repetitora-himiya-ege` (Article #1)
- [ ] `/blog/repetitor-ili-onlain-shkola-himiya` (Article #2)
- [ ] `/blog/zadacha-28-ege-himiya-razbor` (long-tail P0)

### Month 2–3: Scale
- [ ] 2 articles/month per `seo-keywords-research` calendar
- [ ] `/besplatno/diagnosticheskiy-test` lead magnet (5 questions)
- [ ] Programmatic city pages if geo relevant — `mkt-programmatic-seo`

---

## Keyword Priority (next 5 pages to ship)

| Order | URL | Primary keyword | Intent |
|-------|-----|-----------------|--------|
| 1 | `/repetitor-himiya-ege` | репетитор химия егэ | Transactional |
| 2 | `/ceny` | стоимость репетитора химия | Transactional |
| 3 | `/blog/kak-vybrat-repetitora-himiya-ege` | как выбрать репетитора по химии | Info → lead |
| 4 | `/blog/zadacha-28-ege-himiya-razbor` | задача 28 егэ химия | Info → lead |
| 5 | `/o-prepodavatele` | репетитор химия опыт | Trust |

Run keyword validation: `mkt-workflow-seo-keywords` + Wordstat before each publish.

---

## Cannibalization Watch

| Pages | Risk | Mitigation |
|-------|------|------------|
| `/` vs `/zapis` vs future `/repetitor-himiya-ege` | Medium | `/` = brand; `/repetitor-*` = SEO; `/zapis` = form only |
| `/zapis` pricing section vs `/ceny` | Medium | `/ceny` = full detail; `/zapis` = summary + link |
| Blog task articles vs app textbook | Low | Blog = teaser; app = full content, noindex app |

---

## 90-Day SEO Roadmap

| Phase | Goal | KPI |
|-------|------|-----|
| **Aug 2026** | Index-ready site, 5 pages | 0 errors in Webmaster, sitemap submitted |
| **Sep 2026** | 8 pages + 4 blog posts | First impressions in GSC |
| **Oct 2026** | 12+ pages, schema on all money pages | ≥5 organic leads/mo (strategy target) |
| **Nov+ 2026** | Long-tail task articles | 500+ visits/mo |

Aligns with `docs/pm/plan-3months-ads-2026-08-10.md` — SEO complements VK, doesn't replace.

---

## Pre-Launch Checklist (before requesting index)

- [ ] robots.txt blocks `/student`, `/teacher`, `/login`
- [ ] sitemap.xml live at `/sitemap.xml`
- [ ] metadataBase = `https://himych.ru`
- [ ] No 404 in main navigation
- [ ] Yandex Metrika + Webmaster verified
- [ ] Google Search Console verified
- [ ] FAQ schema on `/zapis`
- [ ] Privacy policy complete (152-ФЗ)
- [ ] `site:himych.ru` check — only marketing URLs indexed

---

## Next Steps (skills)

| Step | Skill |
|------|-------|
| Implement robots/sitemap/noindex | dev (`incremental-implementation`) |
| FAQ + Person schema | `mkt-workflow-seo-schema` |
| Optimize `/zapis` meta | `mkt-workflow-seo-optimize` |
| Keyword validation | `mkt-workflow-seo-keywords` |
| First blog article | `mkt-workflow-content-blog` |
| Competitor SERP deep dive | `mkt-workflow-seo-competitor` |

---

## Unresolved Questions

1. **Prod URL live?** himych.ru deployed on Timeweb — needed for GSC/Webmaster
2. **Город в SEO?** Strategy draft says «уточнить город» — affects local keywords
3. **Один домен или split** app/marketing? Currently monorepo single deploy — confirm noindex strategy sufficient
4. **Wordstat validation** — run for P0 keywords before writing titles
