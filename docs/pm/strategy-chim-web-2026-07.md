# Product Strategy: chim_web (Химыч)

**Дата:** 29.07.2026  
**Stage:** MVP → Growth (продукт построен, фокус — GTM и масштабирование репетиторского бизнеса)  
**Author:** Роман (основатель / преподаватель / solo-dev)  
**Триггер:** Annual planning, выбор между solo / сеть учителей / онлайн-школа; запуск маркетинга (VK, TG, реклама с августа)

**Связанные документы:**
- [Discovery Plan](./discovery-chim-web-2026-07.md)
- [Product Discovery (SWOT)](../strategy/product-discovery.md)
- [Монетизация и сеть учителей](../strategy/monetization-teacher-network.md)
- [SEO-стратегия](../strategy/seo-strategy.md)
- [Telegram playbook](../marketing/telegram-channel-playbook.md)

---

## Executive Summary (1 страница)

**chim_web** — не «ещё один EdTech SaaS», а **операционная система репетитора по химии**: живые занятия + собственная платформа (учебник, тесты ЕГЭ/ОГЭ, ДЗ, AI под контролем преподавателя).

**Стратегический выбор на 12–18 мес:** **Premium value + sales-led growth** — продавать связку «репетитор + методика + платформа», а не лицензию софта или массовый курс.

**Последовательность масштаба:**
1. Solo + platform (удержание, bundle)
2. Multi-channel GTM (SEO, VK/TG, реклама, сарафан)
3. Сеть учителей на готовых материалах (12+ мес)
4. Бренд онлайн-школы (18+ мес)

**North Star (бизнес):** количество **активных платящих учеников** с retention ≥ 4 мес.  
**OMTM Q3 2026:** заявки/мес с non-Профi.ру каналов.

**Главное «нет»:** не массовый freemium, не найм учителей до потока лидов, не AI без контроля преподавателя.

---

## 1. Vision

> **Каждый ученик по химии получает личного проводника к ЕГЭ/ОГЭ — с системой подготовки, которая не теряет прогресс между занятиями.**

Мы верим, что подготовка к экзамену — это не банк задач и не вебинар на 500 человек, а **отношения + дисциплина + обратная связь**. Платформа существует, чтобы усилить репетитора, а не заменить его.

**Эмоциональный якорь для родителя:** «Я вижу, что происходит между уроками — и знаю, за что плачу.»

---

## 2. Target Segments

| Segment | JTBD | Size (оценка) | Pain | Alternative today | Priority |
|---------|------|---------------|------|-------------------|----------|
| **A. Родитель 10–11 класс** | «Хочу, чтобы ребёнок сдал химию на 70+ без моего микроменеджмента» | ~130k сдающих ЕГЭ химию/год; SAM — онлайн-репетитор ~15–25k семей | Не понимает прогресс; боится «деньги впустую» | Умскул, репетитор с Профi.ру, школьный учитель | **Primary** |
| **B. Ученик 10–11** | «Хочу понять химию, а не зубрить; нужна практика между уроками» | Подмножество A | Скука, страх органики/расчётов | YouTube, Решу ЕГЭ, чат GPT | Secondary (через A) |
| **C. Родитель 8–9 (ОГЭ)** | «Подготовить к ОГЭ без паники в 9 классе» | Меньше чек, длиннее цикл | Поздно начали | Школа + репетитор | Tertiary (2027+) |
| **D. Нанятый учитель (будущее)** | «Вести занятия по готовой методике без подготовки с нуля» | 5–20 человек за 2 года | Нет клиентов, нет материалов | Свой путь, франшизы | Phase 3 |

**Primary segment:** родитель ученика 10–11 класса, онлайн по РФ (или гибрид с городом), готов платить 2 500–3 500 ₽/ч за **результат + контроль**.

**Explicitly NOT serving (сейчас):**
- Массовый рынок «курс за 15k/год без репетитора» — конкурируем не ценой, а персонализацией
- B2B школьные лицензии на 500+ учеников — другая операционка
- Self-serve «купил подписку на app без репетитора» — нет GTM и support
- Другие предметы — размывание фокуса

---

## 3. Pain Points & Value Created

### Segment A — Родитель

| Pain | Cost of pain | Value chim_web + репетитор |
|------|--------------|----------------------------|
| Не видит прогресс между занятиями | Тревога, смена репетитора, потеря денег | ДЗ, тесты, streak, отчёты; прозрачность |
| Не знает, кого выбрать на Профi.ру | Время, риск «не того» репетитора | 8 лет опыта + платформа + диагностика |
| Ребёнок «бросает» после 2–3 занятий | Потерянный стартовый пакет | Онбординг в app, геймификация, группы |
| Страх органики и расчётов (27–34) | Низкий балл, стресс | Специализация ЕГЭ/ОГЭ, банк задач, AI по учебнику |

### Segment B — Ученик

| Pain | Value |
|------|-------|
| Скучно зубрить | Stepik-тесты, мгновенная проверка |
| Не понимают ошибку | AI-советчик после ошибки (под контролем учителя) |
| Нет структуры | Учебник 31 тема + программа на год |

### Relative cost position

**Premium value** (как Starbucks, не Southwest): не дешевле рынка, а **больше ценности за разумную премию** — bundle «занятия + платформа + контроль».

| | Умскул / массовый курс | Профi.ру репетитор | **Химыч + chim_web** |
|---|------------------------|-------------------|----------------------|
| Цена | 15–40k ₽/год | 1 500–3 000 ₽/ч | 2 500–3 500 ₽/ч + platform |
| Персонализация | Низкая | Высокая (если повезло) | **Высокая + система** |
| Между занятиями | Записи, тесты | Часто ничего | **App, ДЗ, AI, рейтинг** |

---

## 4. Value Propositions (JTBD)

**For родителя:**  
When *ребёнок готовится к ЕГЭ по химии и я не понимаю, есть ли прогресс*, they want *прозрачность и предсказуемый план*, so they can *спокойно платить за занятия, зная что между уроками ребёнок работает*.

**For ученика:**  
When *я готовлюсь к ЕГЭ и теряюсь в органике/расчётах*, they want *понятные объяснения и практику без стыда*, so they can *уверенно идти на экзамен*.

**For будущего учителя (Phase 3):**  
When *я хочу вести химию, но нет клиентов и материалов*, they want *готовую методику + лиды + платформу*, so they can *зарабатывать, фокусируясь на pedagogy, не на ops*.

**Alternatives map:**

| Alternative | Почему выбирают | Наш контр-аргумент |
|-------------|-----------------|-------------------|
| Умскул | Дешевле, бренд | «500 на потоке vs ваш ребёнок + контроль ДЗ» |
| Профi.ру репетитор | Привычно | «+ платформа, программа на год, AI под контролем» |
| YouTube + Решу ЕГЭ | Бесплатно | «Нет обратной связи и плана под уровень» |
| ChatGPT | Быстро | «Галлюцинации, нет программы, списывание» |

---

## 5. Strategic Trade-offs

| We Choose | Over | Because |
|-----------|------|---------|
| **Живой репетитор + platform** | Pure SaaS / self-serve app | Деньги и дифференциация — в занятиях; app усиливает LTV |
| **Ниша химия ЕГЭ/ОГЭ** | Все предметы / все классы | Глубина контента = moat и SEO |
| **Sales-led GTM** (диагностика → пробное) | Product-led freemium | Репетиторство = high-touch; freemium без воронки сливает контент |
| **Premium bundle** | Демпинг vs Профi.ру | Низкая цена не масштабирует solo; ценность в системе |
| **AI под контролем учителя** | «AI решает всё» | Репутация, ПДн, родители боятся списывания |
| **SEO + owned channels** (TG, VK) | Зависимость от Профi.ру | Owned audience = compound interest |
| **Solo + groups сначала** | Найм учителей сейчас | Нет лидов — учители простаивают |
| **Закрытый контент в app** | Индексировать всё в SEO | Причина платить за репетитора |
| **Solo-dev скорость** | Feature parity с Умскул | Выигрываем focus, не breadth |

---

## 6. Key Metrics

### North Star Metric

**Active Paying Students (APS)** — ученики с ≥1 оплаченным занятием в последние 30 дней и ≥1 активностью в app за 14 дней.

*Почему:* объединяет revenue (занятия) и product value (engagement между уроками).

### OMTM по фазам

| Фаза | OMTM | Target |
|------|------|--------|
| Q3 2026 (авг–окт) | Заявки/мес (all channels) | 8–12 |
| Q4 2026 | % лидов non-Профi.ru | ≥40% |
| Q1 2027 | APS + WAU учеников в app | WAU ≥50% APS |
| Q2 2027 | CAC (paid) / LTV | CAC < 50% LTV |

### Input Metrics

| Lever | Metric |
|-------|--------|
| Acquisition | Заявки/мес по каналу (UTM) |
| Activation | Заявка → пробное ≤7 дней |
| Conversion | Пробное → оплата пакета |
| Engagement | ДЗ/нед на ученика, streak |
| Retention | Ученик ≥4 мес, churn после 1 мес |
| Referral | % новых «сарафан» |

### Health Metrics (guardrails)

- NPS родителей ≥8
- AI-диалоги без жалоб на «списывание»
- Время ответа на заявку <2 ч
- % учеников с 0 активностью в app 14 дней <30%

---

## 7. Growth Engine

**Model:** Sales-Led Growth с Product-Assisted Retention.

```
Acquire → Activate → Retain → Expand → Refer
```

### Acquire (2026–2027)

| Channel | Role | Phase |
|---------|------|-------|
| Профi.ру (optimize) | Cash flow, baseline | Now |
| Сарафан + referral | Lowest CAC | Q1 |
| Telegram @himich_teacher | Trust, warm audience | Q1 |
| VK organic + VK Ads | Parents, geo | Aug 2026 |
| SEO site + blog | Compound, long-tail | Q1–Q4 |
| Yandex Direct | Scale proven offer | Q3 pilot |
| MAX | Experimental repost | Low |
| Group enrollment campaigns | Sep, Jan peaks | Recurring |

**Offer (единый):** «Бесплатная диагностика 30 мин → план → пробное → пакет занятий + доступ к платформе».

### Activate

- Пробное → аккаунт chim_web в тот же день
- Welcome-онбординг + 1 ДЗ в первые 24 ч
- Родителю: «что ребёнок сделал за неделю» (manual → кабинет позже)

### Retain

- Еженедельные ДЗ, streak, рейтинг
- Группы для social proof
- Bundle pricing

### Expand

- Индив → группа
- ОГЭ → ЕГЭ (семья остаётся)
- Phase 3: учитель берёт overflow лидов

### Refer

- «Приведи одноклассника → −500 ₽ / бесплатное занятие»

### Unit economics (targets)

| Metric | Target |
|--------|--------|
| LTV (инд., 6 мес) | 45–60k ₽ |
| CAC organic | <5k ₽ |
| CAC paid (VK/Direct) | 15–25k ₽ |
| Payback | 3–6 мес |

---

## 8. Core Capabilities

| Capability | Build / Buy / Partner | Investment | Timeline |
|------------|----------------------|------------|----------|
| Учебник + тесты + ДЗ | **Built** ✅ | — | Done |
| Multi-teacher isolation | **Built** ✅ | — | Done |
| Marketing site + SEO | Build (Tilda→Next) | Medium | Q3 2026 |
| Lead tracking (CRM sheet) | Buy (Notion/Sheets) | Low | Now |
| TG/VK content rhythm | **Partner** (self) | Low | Q3 2026 |
| Paid ads ops | Learn / agency lite | Medium | Aug 2026 |
| Parent dashboard | Build | Medium | 2027 |
| Billing in-app | Defer | — | Not 2026 |
| Teacher onboarding SOP | Build (docs) | Low | 2027 |
| Content autopost bot | Build (approve flow) | Low | Q4 2026 |

**Bottleneck capability:** **GTM / lead generation** — не engineering.

---

## 9. Defensibility

| Moat type | Strength | Evidence |
|-----------|----------|----------|
| **Content** | Strong | 185 лекций, 1680+ заданий, презентации на год, аудио |
| **Methodology** | Strong | 8 лет итераций, не копируется за месяц |
| **Switching costs** | Medium | История прогресса, ДЗ, streak в app |
| **Brand / trust** | Weak→Medium | Рост через TG, SEO, кейсы |
| **Data** | Medium | Результаты учеников, AI-логи, ошибки по темам |
| **Network effects** | Weak | Global leaderboard — minor |
| **Scale economies** | Future | Сеть учителей на shared content |

**Honest assessment:** сегодня moat = **content + methodology + live teacher relationship**. Платформу можно форкнуть; **связку** — сложнее.

**Усиление moat (12 мес):**
1. SEO-бiblioteka разборов (compound)
2. Кейсы результатов (social proof)
3. SOP + презентации для учителей (franchise layer)
4. Parent retention data

---

## Strategic Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| 1 | **Acquisition не масштабируется** — Профi.ру потолок, реклама не окупается | High | Critical | Multi-channel; SEO; kill ads if CAC >30k |
| 2 | **App не используют между занятиями** — bundle не продаётся | Medium | High | E1 metrics; обязательное ДЗ; gamification |
| 3 | **Solo burnout** — преподавание + dev + marketing | High | High | 70/20/10 time; defer bot; groups for ₽/hour |
| 4 | **Качество падает при найме учителей** | Medium | Critical | Pilot 1 teacher; SOP; chim_web monitoring |
| 5 | **AI / ПДн репутация** | Low | High | Teacher logs; no public AI; policy |

---

## Critical Hypotheses

| ID | Hypothesis | Test | Status |
|----|------------|------|--------|
| H1 | Родители платят premium за platform bundle | E2 bundle pitch | 📋 |
| H2 | VK Ads CPL <4k при прогретом VK | Aug pilot | 📋 |
| H3 | SEO ≥2 leads/mo after 15 articles | Q2 2027 | 📋 |
| H4 | WAU ≥50% → retention +2 mo | Activity tracking | 📋 |
| H5 | Teacher on slides ≥80% quality | E4 pilot | 📋 |

---

## Strategic Roadmap Alignment

| Horizon | Strategy focus | Product focus |
|---------|----------------|---------------|
| **0–6 мес** | GTM: VK/TG/SEO/ads, groups | Onboarding, retention metrics |
| **6–12 мес** | Scale acquisition, raise prices | Parent reports, SEO freemium |
| **12–18 мес** | First hired teacher | Teacher SOP, no billing yet |
| **18–24 мес** | School brand | Admin ops, 3–5 teachers |

---

## Next Steps

- [ ] Socialize strategy — проверить trade-offs с реальностью (часы/нед)
- [ ] `pm-workflow-plan-okrs` — OKR на Q3 2026 из Section 6
- [ ] `pm-workflow-value-proposition` — landing copy для VK Ads
- [ ] `pm-workflow-market-scan` — SWOT/PESTLE refresh (optional)
- [ ] `pm-workflow-business-model` — Lean Canvas для investor/partner talk

---

## Condensed Canvas (print-friendly)

```
VISION:     Личный проводник к ЕГЭ + система между занятиями
SEGMENT:    Родитель 10–11, онлайн, premium
VALUE:      Прогресс виден; химия ЕГЭ/ОГЭ; живой учитель + app
TRADE-OFF:  No mass course; no hire before leads; no freemium-first
NORTH STAR: Active Paying Students (engaged)
GROWTH:     Sales-led; VK/TG/SEO/ads/referral
MOAT:       Content + methodology + relationship
RISK #1:    Acquisition
```
