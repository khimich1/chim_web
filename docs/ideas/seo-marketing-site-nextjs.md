# SEO-маркетинговый сайт на Next.js (chim_web)

**Дата:** 29.07.2026  
**Статус:** Решения зафиксированы (idea-refine)  
**Связано:** [plan-3months-ads](../pm/plan-3months-ads-2026-08-10.md), [seo-strategy](../strategy/seo-strategy.md), [seo-keywords-research](../marketing/seo-keywords-research-2026-07.md), [tilda-landing-vk-ads](../marketing/tilda-landing-vk-ads.md)

---

## Problem Statement

**HMW:** Как построить SEO-сайт на своём стеке, который к сезону набора приносит заявки (VK/Direct + органика), не отвлекая от репетиторства больше ~3 ч/нед — при деплое сначала на VPS/IP и покупке домена himych через 1–2 недели?

---

## Recommended Direction

**Marketing slice в существующем monorepo chim_web** — не Tilda, не отдельный Astro-app.

```
frontend/app/(marketing)/     ← indexable: лендинги, блог
frontend/app/login|student|...  ← noindex
content/blog/*.mdx              ← SEO-статьи в git

POST /api/leads → Google Sheet (до домена)
                  → + email mail@himych.ru (после домена)
```

**Почему так:**

| Альтернатива | Почему нет |
|--------------|------------|
| Tilda | Дублирование; отказ в пользу Next |
| Отдельный marketing-app | Overkill при 3 ч/нед |
| Только Taplink/TG | Нет SEO, слабый message match для рекламы |
| Городские landing × N | Онлайн по РФ; риск thin content |

**Moat:** личный репетитор + **реальная платформа** chim_web между занятиями — не wiki как 100points/Степенin.

**Домен и бренд:** `himych.ru` / химыч.рф — совпадает с @himich_teacher.

**География:** один сайт «онлайн по всей России», **без** городских страниц на старте.

**App:** один домен; `/login`, `/student/*`, `/teacher/*` — `robots.txt` + `noindex` (subdomain `app.` — опционально позже).

---

## Key Assumptions to Validate

- [ ] **Домен куплен до 10–12 авг** — иначе VK Ads 15.08 на IP = низкое доверие и проблемы SSL  
  *Тест:* whois + HTTPS на `/zapis`
- [ ] **Форма → Sheet** доставляет заявки без потерь до появления mail@  
  *Тест:* 5 тест-сабмитов с телефона
- [ ] **3 переписанных отзыва** с Profi достаточны для конверсии landing  
  *Тест:* custdev / 2 probables с VK pilot
- [ ] **2 SEO-статьи к 31.08** (задача 28 + выбор репетитора) дают первый органический трафик к окт  
  *Тест:* Вебмастер, ≥10 показов/мес через 8 нед
- [ ] **Точные цены на сайте** не отпугивают (2 500 / 1 500)  
  *Тест:* custdev родителей, E1 CPL

---

## MVP Scope

### In (до 31.08.2026)

| # | Deliverable | Ответственный |
|---|-------------|---------------|
| 1 | `(marketing)/layout` — Metrika (после деплоя), без auth chrome | Cursor |
| 2 | `/zapis`, `/gruppa-ege` — hero, цены, CTA (без фото v1) | Cursor + тексты |
| 3 | `/ceny`, `/repetitor-himiya-ege`, `/o-prepodavatele` | Cursor + тексты |
| 4 | Форма: имя, **телефон**, класс, цель → **Google Sheet** | Cursor |
| 5 | Под формой: кнопки [VK](https://vk.ru/himich_teachr24), @himich_teacher (TG backup) | Cursor |
| 6 | 3 отзыва — переписать с Profi, подпись «— Имя, родитель, N класс» | Вы |
| 7 | `robots.txt`, `sitemap.ts`, metadata, noindex на app routes | Cursor |
| 8 | MDX blog + **2 статьи**: задача 28, как выбрать репетитора | Вы (HL) + Cursor (MDX) |
| 9 | VPS **Timeweb** + docker compose deploy | Вы + Cursor |
| 10 | Цены на сайте: инд. **2 500 ₽/ч**, группа **1 500 ₽/чел × 2 ч** | Контент |

### Out (сентябрь+)

- `mail@himych.ru` + email-уведомления о заявках
- Полная политика конфиденциальности под **152-ФЗ** (с юристом)
- Портретное фото в hero
- `/besplatno/diagnosticheskiy-test` (публичный API к test_ege.db)
- Subdomain `app.himych.ru`
- Городские SEO-страницы
- Autopost-бот (текст + картинка → approve → VK/TG/сайт/Дзен/MAX) — **Q4**
- PostgreSQL таблица `leads`
- Tilda, WordPress, отдельный Astro-app
- 10+ статей до proof of 2 leads/mo organic

---

## Заявки (воронка)

**Primary CTA:** форма с **телефоном** (номер на сайте **не публиковать** — меньше спама, перезвон <2ч).

| Этап | Канал |
|------|-------|
| До домена | Form → **Google Sheet** (новая из `leads-tracker-template.csv`) |
| После домена | Sheet + **mail@himych.ru** |
| Backup | VK, Telegram (не единственный канал — риски TG в РФ) |

---

## Контент-пайплайн

**Август (3 ч/нед):**

```
Вы: HL тем + пример поста
  → Cursor: вёрстка MDX / landing copy
  → Публикация: сайт (+ дубль в TG вручную)
```

**Q4 (vision, не блокер августа):**

```
HL → Cursor/скрипт: черновик + изображение
  → Вы: approve
  → Дубль: сайт, TG, VK, (Дзен/MAX если есть трафик)
```

**Первая очередь SEO:** см. [seo-keywords-research](../marketing/seo-keywords-research-2026-07.md) TOP-10.

---

## Инкременты (связь с plan Q3)

| Срез | Срок | Содержание |
|------|------|------------|
| **0** | до 5.08 | Timeweb VPS, staging IP, `/zapis` + форма → Sheet |
| **1** | до 12.08 | `/gruppa-ege`, `/ceny`, robots, sitemap |
| **2** | **15.08** | **Домен + HTTPS** → VK Ads на `/zapis` (decision gate E1) |
| **3** | до 31.08 | `/repetitor`, `/o-prepodavatele`, MDX + 2 статьи, отзывы |
| **4** | сен | mail@, Метрика цели, статья «выбор репетитора» tune, Direct |

---

## Not Doing (and Why)

| Не делаем | Почему |
|-----------|--------|
| Tilda | Решено: Next в monorepo |
| Публичный телефон на landing | Спам; форма + callback |
| Email до mail@himych.ru | Ваш выбор; Sheet достаточен на 1–2 нед |
| Фото hero v1 | Нет готового фото; не блокирует VK pilot |
| 152-ФЗ full text сейчас | Юрист позже; минимальная ссылка «политика» — stub до готовности |
| Города × N | Онлайн по РФ; thin content |
| TG как единственный lead channel | Риски доступности TG в РФ |
| Полный autopost в августе | Scope creep vs 15.08 |
| Конкурировать с Решу ЕГЭ по тестам | Не ЦА; lead magnet = 5 вопросов позже |

---

## Open Questions

| # | Вопрос | Когда решить |
|---|--------|--------------|
| 1 | Credentials Google Sheet (service account vs Apps Script webhook) | Срез 0 |
| 2 | Точная дата покупки himych.ru | До 10.08 |
| 3 | Stub vs отложить checkbox «согласие на обработку ПД» до 152-ФЗ | Перед prod form |
| 4 | MAX messenger как backup — да/нет | Сентябрь |

---

## Риски

| Риск | Митигация |
|------|-----------|
| IP без домена к 15.08 | Купить домен на нед 1 августа |
| Sheet integration ломается | Fallback: лог в backend + ручной export |
| 3 ч/нед не хватает на 2 статьи | Статья 2 — первая неделя сентября |
| Без фото ниже trust | Сильные отзывы + скрин app (без ФИО) |

---

## Сводка решений (чеклист)

- [x] Стек: Next `(marketing)` + MDX + FastAPI leads
- [x] Домен: himych.ru / химыч.рф
- [x] VPS: Timeweb, неделя 1
- [x] Деплой: IP → домен 1–2 нед
- [x] Leads: форма → Sheet; email после домена
- [x] Телефон: только в форме
- [x] VK: https://vk.ru/himich_teachr24
- [x] TG: @himich_teacher (backup)
- [x] Geo: онлайн РФ, без городов
- [x] Цены: 2 500 / 1 500 публично
- [x] Отзывы: 3 переписанных, имя + класс
- [x] Фото: v1 без фото
- [x] Блог к 31.08: задача 28 + выбор репетитора
- [x] Контент август: HL вручную; automation Q4

---

## Next Step

**Срез 0:** `(marketing)/zapis` + `POST /api/leads` → Google Sheet по спеке [tilda-landing-vk-ads.md](../marketing/tilda-landing-vk-ads.md).
