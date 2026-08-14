# Implementation Plan: SEO-маркетинговый сайт (marketing slice)

**Источник:** [`docs/specs/seo-marketing-site-nextjs.md`](../docs/specs/seo-marketing-site-nextjs.md) v0.1.1 ✅ APPROVED  
**Idea:** [`docs/ideas/seo-marketing-site-nextjs.md`](../docs/ideas/seo-marketing-site-nextjs.md)  
**Landing wireframe:** [`docs/marketing/tilda-landing-vk-ads.md`](../docs/marketing/tilda-landing-vk-ads.md)  
**PM timeline:** [`docs/pm/plan-3months-ads-2026-08-10.md`](../docs/pm/plan-3months-ads-2026-08-10.md)  
**Дата плана:** 2026-07-29  
**Статус:** IMPLEMENT — срез 0 код ✅ (2026-07-29); M-8 deploy — owner  
**Skills:** planning-and-task-breakdown → incremental-implementation → TDD

### Progress

| Срез | Дедлайн | Статус |
|------|---------|--------|
| 0 — `/zapis` + leads | до 05.08 | 🟡 M-1…M-7 ✅ · M-8 owner |
| 1 — landings + SEO infra | до 12.08 | ⬜ |
| 2 — домен + HTTPS + Metrika + VK | **15.08** | ⬜ |
| 3 — SEO pages + blog + reviews | до 31.08 | ⬜ |

| Task | Статус |
|------|--------|
| M-1 Backend leads API | ✅ |
| M-2 Sheet webhook doc | ✅ |
| M-3 Marketing layout | ✅ |
| M-4 LeadForm | ✅ |
| M-5 /zapis | ✅ |
| M-6 /privacy | ✅ |
| M-7 Mini-hub / | ✅ |
| M-8 VPS deploy + Sheet URL | ⬜ owner |

---

## Overview

Вертикальные срезы в monorepo chim_web: route group `(marketing)/`, публичный `POST /api/leads` → Google Sheet (Apps Script webhook), landing pages для VK Ads и SEO, MDX-блог (2 статьи), robots/sitemap/noindex. Один домен `himych.ru`; app routes не индексируются.

**Минимальный демо-путь (срез 0):** родитель открывает `/zapis` → заполняет форму → 201 → строка в Sheet.

**Не в scope августа:** PostgreSQL `leads`, mail@, полная 152-ФЗ, subdomain `app.`, городские страницы.

---

## Architecture Decisions

| Решение | Выбор | Почему |
|---------|--------|--------|
| Hosting | Marketing в том же Next.js + FastAPI | Spec; один docker compose |
| Route groups | `(marketing)/` + существующие `/login`, `/student`, `/teacher` | Минимальный refactor; удалить `app/page.tsx` в пользу `(marketing)/page.tsx` |
| Leads storage | Apps Script webhook → Sheet | OQ-1; быстрый MVP |
| Webhook failure | 201 + structured log | OQ-2; не ломать VK conversion |
| Root `/` | Mini-hub | OQ-3 |
| ПДн | Checkbox + stub `/privacy` | OQ-4 |
| HTTP client | `httpx` (уже в requirements) | Forward webhook |
| Rate limit | slowapi `5/minute` per IP на `/api/leads` | Anti-spam |
| Auth на leads | **Нет** — public endpoint | Marketing funnel |
| MDX | `@next/mdx` + `content/blog/` | Срез 3; не блокирует 0–2 |
| Metrika | Client component, env-gated | Срез 2 после домена |
| TLS | certbot на VPS, отдельный nginx conf | Не менять repo nginx.conf до среза 2 |
| DecorativeBlobs | **Не** на marketing layout | Чистый landing; app сохраняет blobs |

---

## Dependency Graph

```
M-1 Backend leads API (+ pytest)
        │
        ├── M-2 [OWNER] Google Sheet + Apps Script webhook
        │
        ├── M-4 LeadForm + lib/api/leads (+ vitest)
        │         │
        │         └── M-5 /zapis landing
        │
        ├── M-3 Marketing layout (header/footer)
        │         │
        │         ├── M-6 /privacy stub
        │         ├── M-7 / mini-hub
        │         └── M-5
        │
        └── M-8 [OWNER+Cursor] VPS deploy + .env

Slice 0 checkpoint
        │
        ├── M-9  noindex app layouts
        ├── M-10 robots.ts + sitemap.ts
        ├── M-11 /gruppa-ege
        ├── M-12 /ceny
        └── M-13 Platform screenshot block

Slice 1 checkpoint
        │
        ├── M-14 [OWNER] Domain + DNS + certbot
        ├── M-15 химыч.рф 301
        ├── M-16 Metrika + goals
        └── M-17 [OWNER] VK Ads campaign

Slice 2 checkpoint (15.08 gate)
        │
        ├── M-18 MDX infra + blog routes
        ├── M-19 /repetitor-himiya-ege + /o-prepodavatele
        ├── M-20 [OWNER] 2 blog articles content
        ├── M-21 [OWNER] 3 reviews text
        └── M-22 Schema.org + Search Console

Slice 3 checkpoint (31.08)
```

**Параллельно безопасно:** M-2 (owner) пока Cursor делает M-1; M-20/M-21 (контент) пока Cursor делает M-18.

---

## Owner Checklist (не Cursor)

| Когда | Действие | Блокирует |
|-------|----------|-----------|
| Срез 0 | Создать Google Sheet из [`leads-tracker-template.csv`](../docs/marketing/leads-tracker-template.csv) | M-8 prod test |
| Срез 0 | Deploy Apps Script webhook → URL в `.env` | M-8 |
| Срез 0 | Timeweb VPS, `docker compose up`, открыть порт 80 | M-8 |
| 1–5.08 | Купить `himych.ru` + `химыч.рф` | M-14 |
| до 12.08 | DNS A-record → VPS, certbot | M-14 |
| Срез 1 | Скрин student dashboard + blur ФИО → `frontend/public/marketing/` | M-13 |
| Срез 1 | 3 отзыва (переписать с Profi) | M-5 polish / срез 3 |
| Срез 3 | HL тексты 2 статей | M-20 |
| 15.08 | VK Ads → `https://himych.ru/zapis?utm_*` | M-17 |
| После домена | Яндекс.Метрика counter ID → env | M-16 |

---

## Slice 0 — до 05.08

**Goal:** staging на VPS (IP ok), `/zapis` + форма → Sheet, 5 тест-сабмитов.

---

### Task M-1: Backend `POST /api/leads`

**Description:** Pydantic schema, `LeadService` (normalize phone, map row, httpx webhook), router с rate limit. TDD: pytest first. Soft-fail: webhook error → log + still 201.

**Acceptance criteria:**
- [ ] `POST /api/leads` valid body → 201 `{id, status: "accepted"}`
- [ ] Phone `8 (900) 123-45-67` → stored/sent as `+79001234567`
- [ ] Invalid phone / empty name → 422
- [ ] Rate limit: 6th request/minute → 429
- [ ] Webhook mock fails → 201 + error log line with lead payload id
- [ ] Router registered in `main.py`; OpenAPI visible at `/docs`

**Verification:**
- [ ] `pytest tests/test_leads.py -q`
- [ ] `ruff check backend/app/api/routers/leads.py backend/app/services/lead_service.py`

**Dependencies:** None

**Files:**
- `backend/app/schemas/leads.py`
- `backend/app/services/lead_service.py`
- `backend/app/api/routers/leads.py`
- `backend/app/core/config.py` — `google_sheets_webhook_url: str | None`
- `backend/app/main.py`
- `backend/tests/test_leads.py`
- `.env.example` — `GOOGLE_SHEETS_WEBHOOK_URL=`

**Scope:** M (4–6 files)

---

### Task M-2: [OWNER] Google Sheet + Apps Script

**Description:** Инструкция в `docs/marketing/google-sheet-webhook-setup.md` (создать при M-1). Owner: Sheet, script `doPost`, deploy Web App, скопировать URL.

**Acceptance criteria:**
- [ ] Sheet с заголовками из template
- [ ] curl POST на webhook → новая строка
- [ ] URL в VPS `.env` как `GOOGLE_SHEETS_WEBHOOK_URL`

**Verification:**
- [ ] 1 manual curl + 1 submit с телефона

**Dependencies:** None (parallel with M-1)

**Files:**
- `docs/marketing/google-sheet-webhook-setup.md` (Cursor writes guide)

**Scope:** S (doc) + owner ops

---

### Task M-3: Marketing layout shell

**Description:** `(marketing)/layout.tsx` — header (logo «Химыч», ссылки), footer (VK, TG, privacy), без auth chrome и без `DecorativeBlobs`. Shared `MarketingHeader`, `MarketingFooter`.

**Acceptance criteria:**
- [ ] `/zapis` renders inside marketing chrome
- [ ] Footer links: VK `https://vk.ru/himich_teachr24`, TG `@himich_teacher`, `/privacy`
- [ ] No login button prominent in header (optional small «Вход для учеников» → `/login`)

**Verification:**
- [ ] `npm run build`
- [ ] vitest smoke for header/footer if non-trivial

**Dependencies:** None

**Files:**
- `frontend/app/(marketing)/layout.tsx`
- `frontend/components/marketing/MarketingHeader.tsx`
- `frontend/components/marketing/MarketingFooter.tsx`
- Delete or replace `frontend/app/page.tsx` (conflict with `(marketing)/page.tsx`)

**Scope:** M (3–5 files)

---

### Task M-4: LeadForm + API client

**Description:** Client component: поля name, phone, class select, goal select, optional comment, **required** privacy checkbox. Capture UTM from `useSearchParams`. Submit via `lib/api/leads.ts`. States: idle, submitting, success, error.

**Acceptance criteria:**
- [ ] Submit disabled until privacy checked
- [ ] Success message: «Спасибо! Перезвоним в течение 2 часов»
- [ ] UTM query params forwarded in payload
- [ ] `source_page` prop from parent page

**Verification:**
- [ ] `npm run test -- LeadForm`
- [ ] MSW or fetch mock in test

**Dependencies:** M-1 (API exists for integration manual test)

**Files:**
- `frontend/components/marketing/LeadForm.tsx`
- `frontend/components/marketing/LeadForm.test.tsx`
- `frontend/lib/api/leads.ts`

**Scope:** M (3 files)

---

### Task M-5: Landing `/zapis`

**Description:** Server page по wireframe [`tilda-landing-vk-ads.md`](../docs/marketing/tilda-landing-vk-ads.md) §3 — v1 без hero photo: Hero+form, social proof (placeholder или owner reviews later), 3 features, pricing 2500/1500, FAQ (5), final CTA. Metadata + canonical.

**Acceptance criteria:**
- [ ] H1 contains «диагностика»
- [ ] Form above fold on 375px width (mobile-first CSS)
- [ ] Prices visible: 2 500 ₽/ч, 1 500 ₽/чел × 2 ч
- [ ] VK + TG under form with `target="_blank"` + `rel="noopener"`
- [ ] `export const metadata` with title/description from spec

**Verification:**
- [ ] `npm run build`
- [ ] Manual DevTools iPhone SE screenshot

**Dependencies:** M-3, M-4

**Files:**
- `frontend/app/(marketing)/zapis/page.tsx`
- Optional shared: `PricingCards.tsx`, `FaqAccordion.tsx`, `ReviewCard.tsx`

**Scope:** M–L (3–6 files)

---

### Task M-6: Stub `/privacy`

**Description:** Minimal privacy page + link from form checkbox. Placeholder text (1 абзац) — owner can edit copy later.

**Acceptance criteria:**
- [ ] `/privacy` returns 200 with Russian stub text
- [ ] Linked from LeadForm checkbox

**Verification:**
- [ ] `npm run build`

**Dependencies:** M-3

**Files:**
- `frontend/app/(marketing)/privacy/page.tsx`

**Scope:** XS

---

### Task M-7: Mini-hub `/`

**Description:** Replace dev stub home with marketing hub: кто вы, 3 bullets, CTA buttons → `/zapis`, `/ceny` (ceny link ok even if page comes slice 1), `/blog` (placeholder ok until slice 3).

**Acceptance criteria:**
- [ ] `/` shows brand «Химыч», not «chim_web API»
- [ ] Primary CTA → `/zapis`
- [ ] Indexed metadata (title/description)

**Verification:**
- [ ] `npm run build`
- [ ] `/` and `/zapis` both 200

**Dependencies:** M-3

**Files:**
- `frontend/app/(marketing)/page.tsx`
- Remove `frontend/app/page.tsx`

**Scope:** S

---

### Task M-8: Deploy slice 0 on VPS

**Description:** Extend docker `.env` with webhook URL; document VPS steps in plan or `docs/marketing/deploy-vps.md`. Owner runs deploy; Cursor ensures compose builds with new env vars.

**Acceptance criteria:**
- [ ] `docker compose up --build` green locally
- [ ] VPS: `http://<IP>/zapis` 200
- [ ] End-to-end submit → Sheet row

**Verification:**
- [ ] 5 test submits from phone (owner)
- [ ] `pytest` + `npm run build` green before deploy

**Dependencies:** M-1, M-2, M-5, M-7

**Files:**
- `.env.example`
- `docker-compose.yml` (if backend needs new env passthrough)
- Optional: `docs/marketing/deploy-vps.md`

**Scope:** S + owner ops

---

### Checkpoint: Slice 0 (после M-1…M-8)

- [ ] US-M-1, US-M-2, US-M-6 partially met
- [ ] SC-1 (HTTP IP), SC-2, SC-6, SC-9
- [ ] Owner: webhook URL set, 5 Sheet rows
- [ ] **Review:** готовы к slice 1?

---

## Slice 1 — до 12.08

**Goal:** второй landing, цены, SEO infra, noindex app.

---

### Task M-9: noindex on app routes

**Description:** Add `metadata.robots = { index: false, follow: false }` to `login`, `student`, `teacher` layouts.

**Acceptance criteria:**
- [ ] View-source `/login` contains `noindex`
- [ ] Same for `/student`, `/teacher`

**Verification:**
- [ ] `npm run build` + manual view-source

**Dependencies:** Slice 0 checkpoint

**Files:**
- `frontend/app/login/page.tsx` or layout if added
- `frontend/app/student/layout.tsx`
- `frontend/app/teacher/layout.tsx`

**Scope:** S (3 files)

---

### Task M-10: `robots.ts` + `sitemap.ts`

**Description:** Next.js metadata routes. Sitemap: marketing URLs only; dynamic base URL from env `NEXT_PUBLIC_SITE_URL` or request host.

**Acceptance criteria:**
- [ ] `/robots.txt` Disallow `/login`, `/student`, `/teacher`, `/api/`
- [ ] `/sitemap.xml` includes `/`, `/zapis`, `/ceny`, `/gruppa-ege`; excludes `/login`
- [ ] Before domain: sitemap uses staging URL or relative — document behavior

**Verification:**
- [ ] `npm run build`; curl localhost/sitemap.xml

**Dependencies:** M-9

**Files:**
- `frontend/app/robots.ts`
- `frontend/app/sitemap.ts`

**Scope:** S

---

### Task M-11: Landing `/gruppa-ege`

**Description:** Landing B from tilda spec §4 — hero «группа», badge «Старт 1 сентября · 3 места», shared form/pricing components.

**Acceptance criteria:**
- [ ] H1 contains «группа»
- [ ] Same LeadForm + metadata pattern as `/zapis`
- [ ] Message match for VK creative B

**Verification:**
- [ ] `npm run build`; mobile check

**Dependencies:** M-4, M-5 patterns

**Files:**
- `frontend/app/(marketing)/gruppa-ege/page.tsx`

**Scope:** M

---

### Task M-12: Page `/ceny`

**Description:** Dedicated pricing + formats page for SEO query «стоимость репетитора химия».

**Acceptance criteria:**
- [ ] Prices 2500 / 1500 prominent
- [ ] CTA → `/zapis`
- [ ] Unique metadata

**Verification:**
- [ ] In sitemap after M-10

**Dependencies:** M-10

**Files:**
- `frontend/app/(marketing)/ceny/page.tsx`

**Scope:** S–M

---

### Task M-13: Platform screenshot block

**Description:** Add block 4 from tilda spec to `/zapis` (and optionally `/gruppa-ege`): image from `public/marketing/platform-dashboard.webp` (owner provides blurred screenshot).

**Acceptance criteria:**
- [ ] Image with alt text; responsive
- [ ] 4 bullet points about platform
- [ ] No student PII visible

**Verification:**
- [ ] Visual review

**Dependencies:** M-5; **owner image**

**Files:**
- `frontend/app/(marketing)/zapis/page.tsx` (update)
- `frontend/public/marketing/platform-dashboard.webp`

**Scope:** S

---

### Checkpoint: Slice 1 (до 12.08)

- [ ] SC-3, SC-4, SC-7
- [ ] sitemap + robots validated
- [ ] 3 pages ready: `/zapis`, `/gruppa-ege`, `/ceny`

---

## Slice 2 — до 15.08 (VK Ads gate)

**Goal:** HTTPS on `himych.ru`, Metrika, ads live.

---

### Task M-14: [OWNER] Domain + HTTPS

**Description:** DNS A → VPS; certbot; nginx SSL config on server (may live outside repo or as `nginx/nginx.ssl.conf.example`).

**Acceptance criteria:**
- [ ] `https://himych.ru/zapis` 200
- [ ] HTTP → HTTPS redirect
- [ ] `COOKIE_SECURE=true`, `CORS_ORIGINS=https://himych.ru` in prod `.env`

**Verification:**
- [ ] curl -I; browser padlock

**Dependencies:** Slice 1; domain purchased 1–5.08

**Scope:** Owner + optional nginx doc

---

### Task M-15: `химыч.рф` → 301

**Description:** Registrar redirect or nginx server block → `https://himych.ru$request_uri`.

**Acceptance criteria:**
- [ ] `http://химыч.рф/zapis` → `https://himych.ru/zapis`

**Verification:**
- [ ] curl -I

**Dependencies:** M-14

**Scope:** XS (ops)

---

### Task M-16: Яндекс.Метрика

**Description:** `MetrikaScript.tsx` in marketing layout; env `NEXT_PUBLIC_YANDEX_METRIKA_ID`; goals on form success, TG click, VK click.

**Acceptance criteria:**
- [ ] Counter loads only when ID set
- [ ] Dev without ID: no script
- [ ] `lead_form` event on successful submit

**Verification:**
- [ ] Metrika debugger on prod

**Dependencies:** M-14 (prod domain)

**Files:**
- `frontend/components/marketing/MetrikaScript.tsx`
- `frontend/app/(marketing)/layout.tsx`
- `.env.example`

**Scope:** S

---

### Task M-17: [OWNER] VK Ads launch

**Description:** Campaign to `/zapis?utm_source=vk&utm_medium=cpc&utm_campaign=aug2026_diag`; separate ad to `/gruppa-ege`.

**Acceptance criteria:**
- [ ] SC-10: ads do not point to `/` or `/login`
- [ ] UTM appears in Sheet test lead

**Verification:**
- [ ] E1 CPL gate from plan-3months

**Dependencies:** M-14, M-16

**Scope:** Owner

---

### Checkpoint: Slice 2 (**15.08**)

- [ ] US-M-8, SC-1 (HTTPS), SC-8, SC-10
- [ ] **Decision gate E1:** CPL / lead volume per plan-3months

---

## Slice 3 — до 31.08

**Goal:** SEO pages, blog, reviews, Search Console.

---

### Task M-18: MDX blog infrastructure

**Description:** Install `@next/mdx`, configure `next.config.ts`, `lib/blog.ts` for slugs/frontmatter, routes `/blog` and `/blog/[slug]`.

**Acceptance criteria:**
- [ ] MDX file in `content/blog/` renders at `/blog/[slug]`
- [ ] Blog index lists posts by date
- [ ] CTA component → `/zapis` at end of article
- [ ] rehype-sanitize for MDX HTML

**Verification:**
- [ ] `npm run build` with placeholder post

**Dependencies:** Slice 2 checkpoint

**Files:**
- `frontend/next.config.ts`
- `frontend/package.json`
- `frontend/lib/blog.ts`
- `frontend/app/(marketing)/blog/page.tsx`
- `frontend/app/(marketing)/blog/[slug]/page.tsx`
- `frontend/content/blog/.gitkeep` or placeholder

**Scope:** M–L

---

### Task M-19: SEO pages `/repetitor-himiya-ege` + `/o-prepodavatele`

**Description:** Commercial + trust pages; reuse pricing/CTA/reviews components.

**Acceptance criteria:**
- [ ] Unique metadata per URL map in spec
- [ ] In sitemap
- [ ] CTA → `/zapis`

**Verification:**
- [ ] build + sitemap check

**Dependencies:** M-10, M-18 optional parallel

**Files:**
- `frontend/app/(marketing)/repetitor-himiya-ege/page.tsx`
- `frontend/app/(marketing)/o-prepodavatele/page.tsx`

**Scope:** M

---

### Task M-20: [OWNER] Blog articles × 2

**Description:** Content in MDX: `zadacha-28-ege-himiya`, `kak-vybrat-repetitora-himiya`. Owner writes HL; Cursor formats frontmatter + MDX.

**Acceptance criteria:**
- [ ] SC-5: 2 URLs 200, unique titles
- [ ] Frontmatter: title, description, date, canonical

**Verification:**
- [ ] Search Console URL inspection (owner)

**Dependencies:** M-18

**Scope:** Owner content + S Cursor

---

### Task M-21: [OWNER] 3 reviews on landings

**Description:** Replace placeholder reviews on `/zapis` with real rewritten Profi quotes.

**Acceptance criteria:**
- [ ] Format: «— Имя, родитель, N класс»
- [ ] Minimum 3 on `/zapis`

**Dependencies:** M-5

**Scope:** Owner

---

### Task M-22: Schema.org + Search Console

**Description:** JSON-LD on `/zapis` (Person/LocalBusiness); Article on blog posts. Owner adds property in Search Console.

**Acceptance criteria:**
- [ ] Rich results test passes for Organization/Person
- [ ] Sitemap submitted in GSC / Yandex Webmaster

**Verification:**
- [ ] Google rich results test URL

**Dependencies:** M-19, M-20

**Files:**
- `frontend/components/marketing/JsonLd.tsx` or inline in pages

**Scope:** S

---

### Checkpoint: Slice 3 (31.08)

- [ ] SC-5, all success criteria SC-1…SC-10
- [ ] ≥2 blog posts live
- [ ] Ready for September: mail@, Direct tune

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Domain late | High — VK 15.08 | Buy 1–5.08 (OQ-5) |
| Webhook secret leaked | Med | Rate limit; rotate URL |
| Sheet down, lead lost | Med | 201+log; TG backup; check logs daily in Aug |
| `app/page.tsx` route conflict | Med | M-7 explicitly deletes old page |
| MDX breaks build | Med | Slice 3 only; placeholder post in M-18 |
| No time for 2 articles | Med | Article 2 → Sept week 1 (idea-doc) |

---

## Verification Commands (every slice)

```bash
# Backend
cd backend && pytest -q && ruff check .

# Frontend
cd frontend && npm run test && npm run lint && npm run build

# Docker smoke
docker compose up --build -d
curl -sf http://localhost:8080/zapis | head -5
curl -sf -X POST http://localhost:8080/api/leads \
  -H 'Content-Type: application/json' \
  -d '{"name":"Test","phone":"+79001234567","school_class":"11","goal":"ege","source_page":"/zapis"}'
```

---

## Next Step

**Скажите «срез 0» или «начинай M-1»** — IMPLEMENT с Task M-1 (backend leads) по TDD + incremental-implementation.

Коммиты — только по вашей просьбе.
