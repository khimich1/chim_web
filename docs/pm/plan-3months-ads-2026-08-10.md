# План 3 месяца: август – октябрь 2026 (с платной рекламой)

**Дата:** 29.07.2026 (обновлено 29.07 — сайт Next.js вместо Tilda)  
**Горизонт:** авг – окт 2026 (пик набора + стабилизация)  
**Контекст:** solo-репетитор, chim_web, инд. 2 500 ₽/ч, группа 1 500 ₽/чел × 2 ч  
**Связано:** [seo-marketing-site-nextjs.md](../ideas/seo-marketing-site-nextjs.md), [experiments-aug-2026.md](../marketing/experiments-aug-2026.md), [tilda-landing-vk-ads.md](../marketing/tilda-landing-vk-ads.md) (контент блоков), [seo-keywords-research](../marketing/seo-keywords-research-2026-07.md), [metrics-dashboard](../pm/metrics-dashboard-chim-web-2026-07.md)

**Сайт (решение):** маркетинг + SEO в **Next.js `(marketing)`** на VPS **Timeweb**, домен **himych.ru**, заявки **форма → Google Sheet** (mail@himych.ru — после домена). Спека landing-блоков — [tilda-landing-vk-ads.md](../marketing/tilda-landing-vk-ads.md).

---

## 1. Бенчмарки воронки (на что опираемся)

### 1.1. Воронка «заявка → оплата» (образование / репетитор)

Источник: [BigBen CRM — конверсия от заявки до оплаты](https://bigbencrm.ru/academy/admin/leads/conversion/), [обработка заявок](https://bigbencrm.ru/blog/obrabotka-zayavok/).

| Этап | Слабо | **Норма** | Отлично |
|------|-------|-----------|---------|
| Заявка → дозвон / контакт | <60% | **70–80%** | 85–90% |
| Дозвон → пробное | <40% | **50–70%** | 75–85% |
| Пробное → оплата | <30% | **40–60%** | 65–80% |
| **Итого заявка → оплата** | <10% | **15–25%** | 30–45% |

**Solo-репетитор без админа** — планируем **ниже нормы школы**:

| Этап | План (solo) | Комментарий |
|------|-------------|-------------|
| Заявка → контакт <2ч | **65%** | BigBen: ответ <5 мин → 62% в пробное; у вас цель <2ч |
| Контакт → пробное | **55%** | Диагностика бесплатно снижает барьер |
| Пробное → оплата | **45%** | Зависит от скрипта пробного; звонок родителю после |
| **Итого lead → paid** | **~16%** | 0.65 × 0.55 × 0.45 ≈ 16% |

| Сценарий | Lead → paid | Когда использовать |
|----------|-------------|------------------|
| Пessimistic | **8–10%** | Медленный ответ, слабый landing |
| **Base (план)** | **12–16%** | Next landing + Sheet CRM + <2ч ответ |
| Optimistic | **20–25%** | Ответ <15 мин, 3+ отзыва, сильное пробное |

### 1.2. CPL / CAC по каналам

| Канал | CPL (рынок) | Источник |
|-------|-------------|----------|
| VK Ads, образование (регион, лид-форма) | **650–850 ₽** | [Кейс Тверь, 292 лида](https://ratingruneta.ru/cases/case-16506/) |
| VK Ads, онлайн-школа | до **1 500 ₽** | [Кейс БИТ, VK](https://ads.vk.com/cases/prodvizhenie-onlajn-shkoly-kejs-bit) |
| VK Ads, IT-школа (офлайн филиалы) | **1 500–1 800 ₽** | [Байкал Таргет](https://baikal-target.ru/cases/kejs-vk-ads-prodvizhenie-it-shkoly-45-130-lidov-v-mesyacz-na-filial-i-400-zayavok-na-letnie-kanikuly) |
| Яндекс Директ, EdTech массовый (поиск) | **2 000–2 200 ₽** CPA | [Кейс Синергия](https://marketadv.ru/zayavki-ot-260-rub-reklama-kursy-ege-oge-repetitorstvo/) |
| Яндекс Директ, репетитор / узкая ниша | **2 500–6 000 ₽** | [Обзор 2026](https://new-point.bz/blog/stati-kontekstnoj-reklamy/skolko-stoit-lid-v-kontekstnoj-i-targetirovannoj-reklame-i-pochemu-stoimost-menyaetsya/), [monetization doc](../strategy/monetization-teacher-network.md) |
| Контекст общий рынок 2026 | **1 500–6 000 ₽** | [new-point.bz 2026](https://new-point.bz/blog/stati-kontekstnoj-reklamy/skolko-stoit-lid-v-kontekstnoj-i-targetirovannoj-reklame-i-pochemu-stoimost-menyaetsya/) |

**Важно:** кейсы с CPL 260–500 ₽ — **массовые курсы / РСЯ / холодные офферы**, не частный репетитор по химии на поиске.

### 1.3. Конверсия рекламы (VK)

| Метрика | Значение | Источник |
|---------|----------|----------|
| CTR хорошего креатива (образование) | **2.8–4.2%** | Кейс Тверь |
| Квал-лид (IT-школа VK) | **25–55%** от сырых лидов | Байкал Таргет |

### 1.4. LTV (для окупаемости CAC)

| Формат | Расчёт | LTV |
|--------|--------|-----|
| Индив. | 2 500 × 4 зан/мес × **5 мес** | **50 000 ₽** |
| Индив. консерв. | 2 500 × 3 × 3 | **22 500 ₽** |
| Группа | 1 500 × 2 зан/нед × 4 нед × **5 мес** | **60 000 ₽** |
| **План (mix)** | 70% инд. / 30% группа | **~52 000 ₽** |

**Payback:** CAC < 50% LTV → CAC < **26 000 ₽** — реалистичная цель ([internal benchmark](../strategy/monetization-teacher-network.md)).

**Формула:** `CAC = CPL ÷ (lead → paid %)`

| CPL | При 16% conv | При 12% conv |
|-----|--------------|--------------|
| 800 ₽ | 5 000 ₽ | 6 700 ₽ |
| 1 500 ₽ | 9 400 ₽ | 12 500 ₽ |
| 3 000 ₽ | 18 800 ₽ | 25 000 ₽ |
| 4 000 ₽ | 25 000 ₽ | 33 300 ₽ |

---

## 2. Стратегия бюджета (solo, 3 месяца)

**Принцип:** не «120k/мес как агентства», а **поэтапный пилот → масштаб победителя**. Минимум для обучения алгоритмов VK — **~30k/мес** ([team-b.ru VK](https://team-b.ru/blog/skolko-stoit-reklama-v-vkontakte-polnyy-gid-dlya-biznesa-v-2025-godu/)); для Директа тест — **от 15–30k** ([Yandex Direct](https://direct.yandex.ru/base/articles/stoimost-kontekstnoy-reklamy-v-yandeks-direkte)).

| Месяц | Фокус | Реклама |
|-------|-------|---------|
| **Август** | Прогрев + VK pilot + набор группы | VK only |
| **Сентябрь** | Пик сезона, масштаб VK + pilot Direct | VK + Direct |
| **Октябрь** | Оптимизация, SEO, ретаргет | VK + Direct |

---

## 3. Финансовые вложения (cash)

### 3.1. Рекламные бюджеты по сценариям

| Статья | Мин (осторожный) | **Base (план)** | Агрессивный |
|--------|------------------|-----------------|-------------|
| VK Ads — август (½ мес с 15.08) | 15 000 | **20 000** | 30 000 |
| VK Ads — сентябрь | 25 000 | **35 000** | 50 000 |
| VK Ads — октябрь | 25 000 | **40 000** | 55 000 |
| Яндекс Direct — сентябрь (pilot) | 0 | **15 000** | 25 000 |
| Яндекс Direct — октябрь | 0 | **25 000** | 40 000 |
| **Итого реклама 3 мес** | **65 000** | **135 000** | **200 000** |

### 3.2. Прочие расходы (не реклама)

| Статья | Сумма | Период |
|--------|-------|--------|
| VPS Timeweb (marketing + app) | ~500–800 ₽/мес | **~2 000** за 3 мес |
| Домен himych.ru / химыч.рф | 200–500 ₽/год | **500** |
| Tilda | — | **0** (Next в monorepo) |
| Яндекс.Метрика | 0 | — |
| Canva Pro (опционально) | 0 или 1 200 ₽/мес | 0–3 600 |
| Реферальные бонусы (2–4 срабатывания) | 2 500 ₽ × 3 | **~7 500** |
| Профi.ru комиссия (est. 2–3 новых с Profi) | ~15–20% × ~15k | **~6 000** |
| **Итого non-ads** | | **~16 000–23 000** |

### 3.3. Сводка cash out

| Сценарий | Реклама | Прочее | **Всего cash 3 мес** |
|----------|---------|--------|----------------------|
| Мин | 65 000 | 16 000 | **~81 000 ₽** |
| **Base** | 135 000 | 18 000 | **~153 000 ₽** |
| Агрессивный | 200 000 | 23 000 | **~223 000 ₽** |

**Не включено:** ваше время (контент, диагностики, dev), налоги, комиссия эквайринга.

**Время (оценка):** ~8–10 ч/нед маркетинг ≈ 100–130 ч за 3 мес — амортизация при «своими руками».

---

## 4. Прогноз лидов и учеников (Base-сценарий)

### Допущения Base

| Параметр | Значение |
|----------|----------|
| CPL VK | 1 200 ₽ (авг, обучение) → 1 500 ₽ (сен) → 1 400 ₽ (окт) |
| CPL Direct | — / 3 000 ₽ / 2 800 ₽ |
| Lead → paid | 14% (avg), сентябрь 16% (сезон) |
| Organic leads/mo | 4 → 5 → 6 (TG, Profi, referral, SEO старт) |

### Помесячно

#### Август 2026

| Канал | Бюджет | CPL | Лиды | Paid (14%) |
|-------|--------|-----|------|------------|
| VK Ads | 20 000 | 1 200 | 17 | 2.4 |
| Organic | — | — | 4 | 0.6 |
| **Итого** | **20 000** | | **21** | **~3** |

**Действия:** Срезы 0–2 сайта (см. §6), `/zapis` + `/gruppa-ege`, форма → Sheet, 3 поста TG/VK, E6 группа, E2 bundle.

#### Сентябрь 2026 (пик)

| Канал | Бюджет | CPL | Лиды | Paid (16%) |
|-------|--------|-----|------|------------|
| VK Ads | 35 000 | 1 500 | 23 | 3.7 |
| Direct поиск | 15 000 | 3 000 | 5 | 0.8 |
| Organic | — | — | 5 | 0.8 |
| **Итого** | **50 000** | | **33** | **~5** |

**Действия:** масштаб лучшего креатива VK, landing message match, 2 SEO-статьи, ретаргет VK.

#### Октябрь 2026

| Канал | Бюджет | CPL | Лиды | Paid (14%) |
|-------|--------|-----|------|------------|
| VK Ads | 40 000 | 1 400 | 29 | 4.0 |
| Direct | 25 000 | 2 800 | 9 | 1.3 |
| Organic | — | — | 6 | 0.8 |
| **Итого** | **65 000** | | **44** | **~6** |

### Итого 3 месяца (Base)

| Метрика | Значение |
|---------|----------|
| Рекламный бюджет | 135 000 ₽ |
| Платных лидов | ~83 |
| Organic лидов | ~15 |
| **Всего лидов** | **~98** |
| **Новых платящих** | **~14** |
| Blended CAC (только ads) | 135k / (98×0.14×0.85*) ≈ **13 000 ₽** |
| *85% paid from ads weighted | |

*Упрощение: ~12 платящих с рекламы, CAC ads = 135k/12 ≈ **11 250 ₽**.*

### Сценарии сводная таблица

| | Мин | **Base** | Оптим |
|---|-----|----------|-------|
| Cash total | 81k | **153k** | 223k |
| Лидов | 55 | **98** | 140 |
| Новых учеников | 6–8 | **12–15** | 20–25 |
| CAC (ads) | 18–22k | **11–13k** | 8–10k |
| % non-Profi лидов (окт) | 35% | **45%** | 55% |

---

## 5. P&L ориентир (Base, 3 месяца)

### Доход от новых учеников (первые 3 мес после прихода)

Упрощённо: новый ученик приносит в **первый месяц** ~8–10k ₽ (mix ind/group), далее retention.

| Месяц | Новых | Revenue new (1st month)* | Cumulative new MRR-ish |
|-------|-------|--------------------------|-------------------------|
| Авг | 3 | ~27 000 | 27k |
| Сен | 5 | ~45 000 | 72k |
| Окт | 6 | ~54 000 | 126k |

*3 ind × 10k + group partial.*

### Расход vs доход (только incremental)

| | Авг | Сен | Окт | **3 мес** |
|---|-----|-----|-----|-----------|
| Marketing cash | 22k | 55k | 67k | **144k** |
| Incremental revenue (new) | 27k | 45k | 54k | **126k** |
| **Net incremental** | +4k | -10k | -14k | **-20k** |

**Вывод:** в первые **3 месяца** маркeting может быть **слегка в минусе** на cash basis — это нормально: LTV 50k+ × 14 учеников = **~700k потенциала**, payback 3–6 мес.

| Метрика | Target к 31.10 |
|---------|----------------|
| CAC | < 15 000 ₽ |
| LTV/CAC | > 3× (при LTV 50k) |
| Payback | 4–5 мес |
| APS (total active) | +12–15 к текущей базе |

---

## 6. План по неделям (Base)

### Срезы сайта (Next.js marketing)

| Срез | Срок | Deliverable |
|------|------|-------------|
| **0** | до 5.08 | Timeweb VPS, staging IP, `(marketing)/zapis`, форма → Google Sheet |
| **1** | до 12.08 | `/gruppa-ege`, `/ceny`, `robots.txt`, `sitemap.ts` |
| **2** | **15.08** | **himych.ru + HTTPS** → VK Ads на `/zapis` (gate E1) |
| **3** | до 31.08 | `/repetitor-himiya-ege`, `/o-prepodavatele`, MDX + 2 статьи, 3 отзыва |
| **4** | сен | mail@himych.ru, Метрика цели, 152-ФЗ (юрист), Direct tune |

Детали: [seo-marketing-site-nextjs.md](../ideas/seo-marketing-site-nextjs.md).

### Август

| Нед | Маркeting / сайт | Реклама | Product |
|-----|------------------|---------|---------|
| 1 (29.07–3.08) | **Срез 0** старт, CRM Sheet, TG/VK закреп, E2 | — | — |
| 2 | **Срез 1** `/gruppa-ege`, пост, E6 группа | — | — |
| 3 | Креативы, 3-й пост; **домен himych.ru** (до 10.08) | — | — |
| 4 | **Срез 2** + **VK Ads 20k**, daily CRM | **20k** | WAU E3 |
| 5 | **Срез 3** start, Retro E1, custdev 1 | pause/scale | — |

### Сентябрь

| Нед | Маркeting | Реклама |
|-----|-----------|---------|
| 1–2 | SEO: дожать 2 статьи (28 + выбор репетитора), referral | VK 35k (scale winner) |
| 3 | **Срез 4** mail@, Direct setup, landing tune | Direct 15k start |
| 4 | Retarget VK, group fill #2 | optimize |

### Октябрь

| Нед | Маркeting | Реклама |
|-----|-----------|---------|
| 1–2 | SEO + FAQ landing, 3 custdev | VK 40k + Direct 25k |
| 3 | Monthly metrics retro | cut loser ad sets |
| 4 | Plan Nov (scale/kill), SEO | decision gate |

---

## 7. Decision gates

| Дата | Вопрос | Go | No-go |
|------|--------|-----|-------|
| **31.08** | E1 VK | CPL ≤2k, ≥2 probables | Pause ads, fix landing 2 weeks |
| **30.09** | Direct pilot | CAC ≤25k | Direct off, all-in VK+SEO |
| **31.10** | Q4 budget | Scale to 80k/mo ads | Hold 50k/mo |
| **31.10** | Teacher hire? | ≥5 organic+paid leads/mo | Delay Path C |

---

## 8. Риски и митигация

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| CPL VK >3k | Средняя | Лид-форма VK + landing A/B на `/zapis` |
| Lead→paid <10% | Средняя | Ответ <15 мин, скрипт пробного |
| **Домен не к 15.08** | Средняя | IP только staging; реклама — после HTTPS |
| **Sheet / форма ломается** | Низкая | Fallback: лог backend + ручной export |
| Cash минус 3 мес | Высокая | Cap 135k ads, не агрессивный сценарий |
| Burnout | Высокая | Autopost Q4, не август; dev — Cursor |
| Direct сливает бюджет | Средняя | Только поиск, 5 ключей, cap 15k |
| TG недоступен | Средняя | Основной lead: форма + телефон; VK backup |

---

## 9. KPI dashboard (еженедельно)

См. [metrics-dashboard-chim-web-2026-07.md](../pm/metrics-dashboard-chim-web-2026-07.md).

| KPI | Aug | Sep | Oct |
|-----|-----|-----|-----|
| Leads | 21 | 33 | 44 |
| CPL blended (paid) | 1 200 | 1 800 | 1 600 |
| New paid | 3 | 5 | 6 |
| % non-Profi | 25% | 38% | 45% |
| Marketing spend | 22k | 55k | 67k |
| Site: leads via Sheet | ✓ | + mail@ | + Metrika goals |

---

## 10. Источники бенчмарков

| Тема | URL |
|------|-----|
| CPL контекст 2026 | https://new-point.bz/blog/stati-kontekstnoj-reklamy/skolko-stoit-lid-v-kontekstnoj-i-targetirovannoj-reklame-i-pochemu-stoimost-menyaetsya/ |
| VK образование, CPL 684₽ | https://ratingruneta.ru/cases/case-16506/ |
| VK онлайн-школа | https://ads.vk.com/cases/prodvizhenie-onlajn-shkoly-kejs-bit |
| Воронка заявка→оплата | https://bigbencrm.ru/academy/admin/leads/conversion/ |
| Скорость ответа | https://bigbencrm.ru/blog/obrabotka-zayavok/ |
| ЕГЭ Direct CPA | https://marketadv.ru/zayavki-ot-260-rub-reklama-kursy-ege-oge-repetitorstvo/ |
| Yandex budget min | https://direct.yandex.ru/base/articles/stoimost-kontekstnoy-reklamy-v-yandeks-direkte |

---

## Quick answer

**Сколько закладывать (Base):** **~153 000 ₽ cash** за 3 месяца (135k ads + ~18k VPS/домен/bonus). Tilda **0 ₽**.  
**Ожидание:** **~98 лидов → 12–15 новых учеников**, CAC **~11–13k ₽**, окупаемость **4–6 мес** при LTV ~50k.  
**Первый месяц ads:** **20 000 ₽ VK** с **15.08** на **himych.ru/zapis** после Срезов 0–2 (не IP).  
**Сайт:** Next `(marketing)` на Timeweb — [seo-marketing-site-nextjs.md](../ideas/seo-marketing-site-nextjs.md).
