# Spec: SEO-маркетинговый сайт (Next.js marketing slice)

**Версия:** 0.1.1  
**Дата:** 2026-07-29  
**Статус:** ✅ APPROVED (2026-07-29) → PLAN в [`tasks/plan-seo-marketing-site.md`](../../tasks/plan-seo-marketing-site.md)  
**Источник:** [`docs/ideas/seo-marketing-site-nextjs.md`](../ideas/seo-marketing-site-nextjs.md)  
**Родитель:** [`SPEC.md`](../../SPEC.md) §8 (Деплой), общий monorepo  
**Связано:** [`tilda-landing-vk-ads.md`](../marketing/tilda-landing-vk-ads.md) (wireframe блоков), [`seo-keywords-research-2026-07.md`](../marketing/seo-keywords-research-2026-07.md), [`plan-3months-ads-2026-08-10.md`](../pm/plan-3months-ads-2026-08-10.md)

---

## Assumptions (проверьте до PLAN)

Если не поправите — считаем принятыми:

1. **Один домен** `himych.ru` (и опционально `химыч.рф` → 301 на punycode) для marketing + app. Subdomain `app.` — **не в августе**.
2. **Marketing slice** живёт в том же Next.js-приложении: route group `(marketing)/`, не отдельный repo/app.
3. **App routes** (`/login`, `/student/*`, `/teacher/*`) остаются на том же origin; индексируем только marketing + blog. Защита: `robots.txt` Disallow + `metadata.robots: noindex` на app layouts.
4. **Корень `/`** — **mini-hub** (бренд, ссылки на `/zapis`, `/ceny`, `/blog`), **не** redirect и не dev-заглушка.
5. **Leads MVP:** `POST /api/leads` (FastAPI) → **Google Sheet** через **Apps Script webhook URL** (env `GOOGLE_SHEETS_WEBHOOK_URL`). Service account — отложен. **При сбое webhook:** HTTP **201** клиенту + structured error log (не 503); мониторинг логов вручную до alert в сентябре.
6. **Телефон обязателен** в форме; публичный номер на сайте **не показываем**. Валидация: российский мобильный `+7…` / `8…` (10 цифр после кода).
7. **152-ФЗ:** v1 — **обязательный** checkbox «Согласие на обработку ПД» + stub `/privacy` (1 абзац + контакт). Полный текст с юристом — сентябрь+.
8. **Hero без фото** v1; placeholder или текст-only layout (см. tilda wireframe).
9. **MDX blog:** `@next/mdx` + `content/blog/*.mdx` в git; 2 статьи к 31.08 — контент от владельца, вёрстка/MDX — Cursor.
10. **Яндекс.Метрика** — счётчик только в `(marketing)/layout`; ID из env `NEXT_PUBLIC_YANDEX_METRIKA_ID` (пустой в dev = не грузить скрипт).
11. **Деплой августа:** существующий `docker compose` на **Timeweb VPS**; домен **himych.ru покупается неделя 1 августа (1–5.08)**; HTTPS certbot до VK Ads 15.08.
12. **Landing блок платформы:** реальный скрин student dashboard с **blur ФИО** учеников (срез 1+).
13. **химыч.рф:** купить + **301 redirect** → `himych.ru` (не отдельный сайт).
14. **Бюджет времени:** ~3 ч/нед на контент; код — инкрементами по срезам 0–3 из idea-doc.
15. **Цены публично:** инд. **2 500 ₽/ч**, группа **1 500 ₽/чел × 2 ч** — как в plan-3months.
16. **CORS / API URL:** production `NEXT_PUBLIC_API_URL` = origin сайта (nginx проксирует `/api/*`); форма шлёт на same-origin `/api/leads`.

→ Поправьте нумерованные пункты, иначе после approve идём в PLAN с ними.

---

## 1. Objective

### Что строим

Публичный **SEO + conversion** слой в monorepo chim_web:

| Компонент | Назначение |
|-----------|------------|
| Landing pages | VK/Direct трафик → заявка на бесплатную диагностику |
| SEO pages | Органика по коммерческим запросам («репетитор химия егэ», «цены») |
| MDX blog | Long-tail + доверие (задача 28, выбор репетитора) |
| Lead API | Форма → Google Sheet CRM |
| SEO infra | sitemap, robots, metadata, schema.org basics |

### Зачем

- **VK Ads pilot 15.08** — dedicated landing с message match, не dev-заглушка.
- **Органика к октябрю** — 2 статьи + коммерческие страницы в индексе.
- **Moat** — между landing и конкурентами-wiki видна **реальная платформа** chim_web.

### Для кого

| Персона | Job | Ключевые страницы |
|---------|-----|-------------------|
| **Родитель** (primary) | Найти репетитора, записаться | `/zapis`, `/repetitor-himiya-ege`, `/ceny` |
| **Родитель** (группа) | Записать в группу с 1 сент | `/gruppa-ege` |
| **Родитель / ученик** (SEO) | Разобраться, выбрать | `/blog/*` |
| **Владелец** | Получить заявку <2ч, видеть UTM | Sheet + Metrika |

### User stories + acceptance

| ID | Story | Acceptance |
|----|--------|------------|
| US-M-1 | Родитель с VK попадает на `/zapis?utm_*` | H1 «диагностика» above fold; форма видна на mobile без scroll (iPhone SE) |
| US-M-2 | Родитель отправляет заявку | `POST /api/leads` → 201; строка в Google Sheet с полями из template; UI «Спасибо, перезвоним <2ч» |
| US-M-3 | Sheet недоступен | Пользователь видит success (или мягкую ошибку + TG backup); backend пишет error log |
| US-M-4 | Поисковик индексирует marketing | `/zapis`, `/ceny`, blog в sitemap; `/login`, `/student` — **не** в sitemap, `noindex` |
| US-M-5 | Родитель читает SEO-статью | `/blog/zadacha-28-ege-himiya` рендерится SSG; canonical, title, description; CTA на `/zapis` |
| US-M-6 | Родитель не хочет форму | Кнопки VK + Telegram под формой; Metrika goal `click_telegram` / `click_vk` |
| US-M-7 | Владелец видит рекламную атрибуцию | Sheet: `utm_source`, `utm_campaign`, `source_page`, `submitted_at` |
| US-M-8 | HTTPS на домене к 15.08 | `https://himych.ru/zapis` открывается; редирект HTTP→HTTPS |

### Out of scope (август)

См. idea-doc §Out: mail@, PostgreSQL `leads`, городские страницы, публичный diagnostic test API, autopost, hero photo, full 152-ФЗ, subdomain `app.`.

---

## 2. Tech Stack

| Слой | Стек | Примечание |
|------|------|------------|
| Frontend | Next.js 16 App Router, React 19, Tailwind 4 | Route group `(marketing)/` |
| Blog | `@next/mdx`, `content/blog/*.mdx` | SSG; rehype-sanitize уже в проекте |
| Backend | FastAPI, Pydantic v2, slowapi | Новый router `leads` |
| CRM | Google Sheets + Apps Script | Webhook POST JSON |
| Analytics | Яндекс.Метрика | Только marketing layout |
| Deploy | Docker Compose, nginx, Timeweb VPS | certbot для TLS после домена |
| SEO | `app/sitemap.ts`, `app/robots.ts`, Metadata API | |

**Новые зависимости (ожидаемые):**

| Пакет | Где | Ask first? |
|-------|-----|------------|
| `@next/mdx`, `@mdx-js/react` | frontend | да (package.json) |
| `httpx` (если нет) | backend — forward to webhook | проверить requirements |

---

## 3. Commands

```bash
# Backend (local)
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest tests/test_leads.py -q
ruff check .

# Frontend (local)
cd frontend
npm run dev                    # http://localhost:3000
npm run test -- LeadForm MarketingLayout
npm run lint
npm run build

# Full stack (docker, как prod)
cp .env.example .env           # дополнить GOOGLE_SHEETS_WEBHOOK_URL, METRIKA_ID
docker compose up --build
# http://localhost:8080/zapis

# SEO smoke (после deploy)
curl -s https://himych.ru/robots.txt
curl -s https://himych.ru/sitemap.xml | head
curl -X POST https://himych.ru/api/leads -H 'Content-Type: application/json' \
  -d '{"name":"Test","phone":"+79001234567","school_class":"11","goal":"ege","source_page":"/zapis"}'
```

---

## 4. Project Structure

```
frontend/
  app/
    (marketing)/
      layout.tsx              # Metrika, marketing header/footer, без auth chrome
      page.tsx                # / — hub → CTA /zapis
      zapis/page.tsx          # Landing A (VK primary)
      gruppa-ege/page.tsx     # Landing B
      ceny/page.tsx
      repetitor-himiya-ege/page.tsx
      o-prepodavatele/page.tsx
      privacy/page.tsx        # stub 152-ФЗ
      blog/
        page.tsx              # список статей
        [slug]/page.tsx       # MDX render
    login/                    # + layout metadata noindex
    student/                  # + layout metadata noindex
    teacher/                  # + layout metadata noindex
    robots.ts
    sitemap.ts
    layout.tsx                # root (shared html/body, globals.css)
  components/marketing/
    LeadForm.tsx              # client: form + submit
    LeadForm.test.tsx
    MarketingHeader.tsx
    MarketingFooter.tsx
    PricingCards.tsx
    ReviewCard.tsx
    FaqAccordion.tsx
    MetrikaScript.tsx         # client, conditional on env
  content/blog/
    zadacha-28-ege-himiya.mdx
    kak-vybrat-repetitora-himiya.mdx
  lib/
    api/leads.ts              # submitLead()
    blog.ts                   # load MDX slugs, frontmatter

backend/
  app/
    api/routers/leads.py
    schemas/leads.py
    services/lead_service.py
  tests/test_leads.py

nginx/
  nginx.conf                  # без изменений для MVP (TLS — отдельный conf на VPS)

docs/
  specs/seo-marketing-site-nextjs.md   # этот файл
  marketing/leads-tracker-template.csv # колонки Sheet
```

### URL map (MVP)

| URL | Index | Title (draft) |
|-----|-------|---------------|
| `/` | yes | Химыч — репетитор по химии ЕГЭ и ОГЭ онлайн |
| `/zapis` | yes | Репетитор по химии ЕГЭ — бесплатная диагностика \| Химыч |
| `/gruppa-ege` | yes | Группа ЕГЭ химия с 1 сентября \| Химыч |
| `/ceny` | yes | Цены на занятия по химии \| Химыч |
| `/repetitor-himiya-ege` | yes | Репетитор по химии ЕГЭ онлайн \| Химыч |
| `/o-prepodavatele` | yes | О преподавателе — Роман Алексеевич \| Химыч |
| `/blog`, `/blog/*` | yes | per-article |
| `/privacy` | yes (low prio) | Политика конфиденциальности |
| `/login`, `/student/*`, `/teacher/*` | **no** | — |

Wireframe блоков landing A/B — **не дублировать здесь**; копировать структуру из [`tilda-landing-vk-ads.md`](../marketing/tilda-landing-vk-ads.md) §3–4.

---

## 5. Code Style

Marketing — Server Components по умолчанию; `'use client'` только для формы, FAQ accordion, Metrika.

Переиспользовать design tokens из `globals.css` (`chem-teal`, `chem-btn-primary`, `chem-card`).

### Lead form (frontend)

```typescript
// lib/api/leads.ts
export type LeadPayload = {
  name: string;
  phone: string;
  school_class: "8" | "9" | "10" | "11";
  goal: "ege" | "oge" | "school";
  comment?: string;
  source_page: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
};

export async function submitLead(payload: LeadPayload): Promise<void> {
  const res = await fetch("/api/leads", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("submit_failed");
}
```

### Lead API (backend)

```python
# Router → Service; Pydantic на границе; rate limit на POST
@router.post("/leads", status_code=201, response_model=LeadCreated)
@limiter.limit("5/minute")
async def create_lead(
    request: Request,
    body: LeadCreate,
    service: LeadService = Depends(get_lead_service),
) -> LeadCreated:
    return await service.submit(body, client_ip=request.client.host)
```

```python
class LeadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=10, max_length=20)
    school_class: Literal["8", "9", "10", "11"]
    goal: Literal["ege", "oge", "school"]
    comment: str | None = Field(default=None, max_length=1000)
    source_page: str = Field(max_length=200)
    utm_source: str | None = Field(default=None, max_length=100)
    utm_medium: str | None = Field(default=None, max_length=100)
    utm_campaign: str | None = Field(default=None, max_length=100)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) == 11 and digits.startswith("8"):
            digits = "7" + digits[1:]
        if len(digits) != 11 or not digits.startswith("7"):
            raise ValueError("Invalid RU phone")
        return f"+{digits}"
```

### Marketing layout metadata

```typescript
// app/(marketing)/zapis/page.tsx
export const metadata: Metadata = {
  title: "Репетитор по химии ЕГЭ — бесплатная диагностика | Химыч",
  description: "Определим уровень за 30 минут. Онлайн по всей России. Платформа с ДЗ между занятиями.",
  alternates: { canonical: "/zapis" },
  openGraph: { locale: "ru_RU", type: "website" },
};
```

### App noindex

```typescript
// app/student/layout.tsx (и login, teacher)
export const metadata: Metadata = {
  robots: { index: false, follow: false },
};
```

---

## 6. API Contract: POST /api/leads

### Request

`Content-Type: application/json`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | yes | 1–100 chars |
| `phone` | string | yes | RU mobile, normalized `+7XXXXXXXXXX` |
| `school_class` | enum | yes | `8` \| `9` \| `10` \| `11` |
| `goal` | enum | yes | `ege` \| `oge` \| `school` |
| `comment` | string | no | max 1000 |
| `source_page` | string | yes | e.g. `/zapis` |
| `utm_source` | string | no | from query on client |
| `utm_medium` | string | no | |
| `utm_campaign` | string | no | |

### Response

**201 Created**

```json
{ "id": "uuid", "status": "accepted" }
```

**422** — validation error (standard FastAPI)  
**429** — rate limit

### Google Sheet row mapping

Колонки из [`leads-tracker-template.csv`](../marketing/leads-tracker-template.csv):

| Sheet column | Source |
|--------------|--------|
| `date` | server ISO timestamp (MSK display optional) |
| `name` | `name` |
| `contact` | `phone` |
| `class` | `school_class` |
| `exam` | mapped label from `goal` |
| `source` | `source_page` |
| `utm_source` | `utm_source` |
| `utm_campaign` | `utm_campaign` |
| `notes` | `comment` + optional `utm_medium` |

` trial_date`, `paid`, `bundle` — пустые (заполняет владелец вручную).

### Apps Script webhook (рекомендация среза 0)

- Google Sheet «Leads himych» из template.
- Apps Script `doPost(e)` парсит JSON, appendRow.
- URL деплоится как Web App («Anyone»).
- Backend: `httpx.post(webhook_url, json=row, timeout=10s)`; при ошибке — `logger.error` + **201 клиенту** (решение OQ-2: soft-fail, не блокировать UX рекламы).

**Решение OQ-1:** только Apps Script webhook на MVP; service account — не раньше сентября.

---

## 7. Testing Strategy

| Уровень | Framework | Что покрываем |
|---------|-----------|---------------|
| Backend unit | pytest | phone normalize, schema validation, service mock webhook |
| Backend integration | pytest + TestClient | POST /api/leads 201/422/429 |
| Frontend unit | vitest + RTL | LeadForm validation, success/error states, UTM capture |
| Frontend build | `npm run build` | MDX pages compile, sitemap generates |
| E2E (optional aug) | Playwright | submit form → mock API 201 |
| Manual | browser | mobile `/zapis`, Sheet row, Metrika debugger |

**Coverage expectation:** happy path + validation + rate limit для leads; не гонимся за 100% на marketing static pages.

```bash
pytest tests/test_leads.py -q
cd frontend && npm run test -- LeadForm
```

---

## 8. SEO & Analytics

### robots.txt

```
User-agent: *
Allow: /
Disallow: /login
Disallow: /student
Disallow: /teacher
Disallow: /api/
Sitemap: https://himych.ru/sitemap.xml
```

(На staging IP — `Sitemap` с текущим host или omit до домена.)

### sitemap.ts

Dynamic list: marketing routes + blog slugs from `content/blog/`. **Exclude** app routes.

### Metrika goals (после деплоя)

| ID | Event |
|----|-------|
| G1 | form submit success |
| G2 | click Telegram |
| G3 | click VK |
| G4 | visit `/gruppa-ege` (optional) |

### Schema.org (v1 minimal)

- `LocalBusiness` или `Person` + `Offer` на `/zapis` — name, description, priceRange, areaServed: RU.
- `Article` on blog posts.

---

## 9. Boundaries

### Always

- Rate limit на `POST /api/leads`
- Валидация телефона и длины полей на backend
- `noindex` на app routes
- Marketing pages работают **без auth**
- Не публиковать телефон в footer/hero
- Запуск `pytest` + `npm run build` перед merge среза
- UTM прокидывать с landing query → form → API → Sheet

### Ask first

- Новые npm/pip dependencies (`@next/mdx`, httpx)
- Изменение root `/` поведения (redirect vs hub)
- Checkbox ПДн + текст `/privacy` перед prod
- Покупка/ DNS домена, certbot nginx config
- Credentials Google (webhook URL в `.env`)
- Добавление публичных API endpoints кроме leads

### Never

- JWT / session cookies на marketing pages
- Index app dashboards или `/api/docs` в sitemap
- Commit `.env`, webhook secrets, service account JSON
- Fake scarcity («осталось 1 место» timer)
- Публичный телефон на сайте
- PostgreSQL `leads` table в августе
- Городские thin-content страницы

---

## 10. Implementation Increments (preview для PLAN)

Детальный task breakdown — **фаза TASKS**, после approve spec.

| Срез | Срок | Deliverable | Verify |
|------|------|-------------|--------|
| **0** | до 05.08 | `(marketing)/layout`, `/zapis`, LeadForm, `POST /api/leads` → Sheet, docker on VPS IP | 5 test submits → Sheet; mobile form visible |
| **1** | до 12.08 | `/gruppa-ege`, `/ceny`, robots, sitemap, noindex app | sitemap.xml valid; app routes noindex in HTML |
| **2** | **15.08** | Domain + HTTPS, Metrika, VK Ads on `/zapis` | E1 CPL gate from plan-3months |
| **3** | до 31.08 | `/repetitor-himiya-ege`, `/o-prepodavatele`, MDX + 2 articles, 3 reviews | Search Console URL inspect; 2 blog URLs 200 |

---

## 11. Success Criteria (август MVP)

Конкретные, проверяемые условия «готово»:

| # | Criterion | Check |
|---|-----------|-------|
| SC-1 | `/zapis` deploy на VPS доступен по HTTPS (домен) или HTTP (IP staging) | curl 200 |
| SC-2 | Форма с телефоном отправляется; ≥5 тестовых строк в Sheet | manual + pytest |
| SC-3 | `/login`, `/student` возвращают `noindex` | view-source / Playwright |
| SC-4 | `sitemap.xml` содержит `/zapis`, `/ceny`, blog; **не** содержит `/login` | curl + assert |
| SC-5 | 2 blog URL отдают контент, уникальные title/description | build + manual |
| SC-6 | Landing mobile: форма above fold на 375px width | DevTools screenshot |
| SC-7 | Цены 2 500 / 1 500 видны на `/zapis` и `/ceny` | visual |
| SC-8 | VK + TG backup links работают | click + Metrika test |
| SC-9 | `npm run build` и `pytest` green | CI local |
| SC-10 | VK Ads 15.08 ведёт на `/zapis?utm_*` (не на `/`) | ads config |

**Reframed from vague goals:**

| Vague | Measurable |
|-------|------------|
| «SEO-сайт работает» | SC-3, SC-4, SC-5 + Search Console property added |
| «Заявки не теряются» | SC-2 + Sheet alert on failed webhook (manual check log) |
| «Готов к рекламе» | SC-1, SC-6, SC-10 к 15.08 |

---

## 12. Decisions (закрыто 2026-07-29)

| # | Решение | Выбор |
|---|---------|-------|
| OQ-1 | Sheet integration | **Apps Script webhook** |
| OQ-2 | Webhook failure UX | **201 + structured log** (не 503) |
| OQ-3 | Root `/` | **Mini-hub** (не redirect) |
| OQ-4 | ПДн | **Checkbox + stub `/privacy`** |
| OQ-5 | Покупка himych.ru | **Неделя 1 августа (1–5.08)** |
| OQ-6 | Скрин платформы | **Реальный скрин, blur ФИО** |
| OQ-7 | химыч.рф | **Купить + 301 → himych.ru** |

### Остаётся открытым

| # | Вопрос | Когда |
|---|--------|-------|
| — | Точный день покупки домена в окне 1–5.08 | Вы |
| — | Текст stub `/privacy` (1 абзац) | Перед prod form |
| — | Alert при сбое webhook (email/TG) | Сентябрь+ (опционально) |

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| IP без TLS к 15.08 | Купить домен нед 1 августа; certbot |
| Sheet webhook down | Backend log + TG backup CTA |
| MDX scope creep | Ровно 2 slugs; шаблон frontmatter |
| App leaked to index | robots + noindex + Search Console inspect |
| 3 ч/нед не хватает | Статья 2 → первая неделя сентября (idea-doc) |

---

## Next Step

1. ~~Финальный approve spec~~ ✅ 2026-07-29
2. **PLAN** — [`tasks/plan-seo-marketing-site.md`](../../tasks/plan-seo-marketing-site.md)
3. **Реализация** — срез 0: «начни срез 0» / Task M-1
