import type { Metadata } from "next";
import Image from "next/image";

import { FaqAccordion } from "@/components/marketing/FaqAccordion";
import { LeadFormSection } from "@/components/marketing/LeadFormSection";

const TEACHER_PORTRAIT = "/marketing/teacher-portrait.jpg";

export const metadata: Metadata = {
  title: "Репетитор по химии ЕГЭ — бесплатная диагностика | Химыч",
  description:
    "Определим уровень за 30 минут. Онлайн по всей России. Платформа с ДЗ между занятиями.",
  alternates: { canonical: "/zapis" },
  openGraph: {
    locale: "ru_RU",
    type: "website",
    images: [{ url: TEACHER_PORTRAIT, alt: "Роман Алексеевич — репетитор по химии" }],
  },
};

const HERO_BULLETS = [
  "Индивидуально и группы 4–6 человек",
  "Программа на весь год — не хаотичные темы",
  "Между занятиями: учебник, тесты, домашние задания в одном месте",
] as const;

const FEATURES = [
  {
    title: "30 минут по Zoom",
    text: "Разберём 2–3 типовых задания, без стресса «экзамена»",
  },
  {
    title: "Честный уровень",
    text: "Скажем, реально ли цель 70+ / 80+ к вашей дате",
  },
  {
    title: "План на 2–3 месяца",
    text: "Какие темы закрыть первыми — не «всё подряд»",
  },
] as const;

const REVIEWS = [
  {
    quote:
      "Сын наконец понял органику — после двух месяцев занятий оценка выросла с 3 до 5.",
    author: "Елена, родитель, 11 класс",
  },
  {
    quote:
      "Понравилась платформа: видно, что сделано между уроками, не нужно искать файлы в чатах.",
    author: "Ольга, родитель, 10 класс",
  },
  {
    quote: "Спокойно объясняет, без давления. Ребёнок сам просит дополнительные задания.",
    author: "Игорь, родитель, 9 класс",
  },
] as const;

const FAQ_ITEMS = [
  {
    question: "Это бесплатная диагностика — потом обязательно платить?",
    answer:
      "Нет. После диагностики вы сами решаете — подходит формат или нет.",
  },
  {
    question: "Онлайн или очно?",
    answer:
      "Онлайн (Zoom / аналог). Очно — по договорённости, уточняйте в сообщении.",
  },
  {
    question: "Какой класс нужен для старта?",
    answer:
      "Оптимально с 10 класса для ЕГЭ; в 11 — тоже, если готовы к интенсиву.",
  },
  {
    question: "Чем отличаетесь от Умскула?",
    answer:
      "Не поток на 500 человек — живой репетитор, ваш ребёнок, программа под уровень.",
  },
  {
    question: "Как часто занятия?",
    answer: "Обычно 1–2 раза в неделю + работа на платформе между уроками.",
  },
] as const;

export default function ZapisPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-12">
      {/* Hero: mobile — H1 → form → bullets; desktop — text+bullets | form */}
      <section className="grid gap-6 lg:grid-cols-2 lg:items-start lg:gap-8">
        <div className="order-1 lg:col-start-1 lg:row-start-1">
          <p className="chem-kicker">Онлайн по всей России</p>
          <h1 className="mt-2 text-3xl font-semibold leading-tight text-zinc-900 sm:text-4xl">
            Репетитор по химии ЕГЭ и ОГЭ
            <span className="mt-1 block text-chem-teal-dark">
              Бесплатная диагностика 30 минут
            </span>
          </h1>
          <p className="mt-4 text-base text-zinc-600 sm:text-lg">
            Определим уровень, разберём слабые темы и составим план подготовки.
            8 лет опыта · личная платформа с ДЗ между уроками.
          </p>
        </div>

        <div
          id="form"
          className="order-2 scroll-mt-4 lg:col-start-2 lg:row-span-2 lg:row-start-1"
        >
          <LeadFormSection
            sourcePage="/zapis"
            formId="hero-form"
            showSocialLinks={false}
          />
        </div>

        <ul className="order-3 space-y-2 text-sm text-zinc-700 sm:text-base lg:col-start-1 lg:row-start-2">
          {HERO_BULLETS.map((item) => (
            <li key={item} className="flex gap-2">
              <span className="text-chem-teal" aria-hidden="true">
                ✓
              </span>
              {item}
            </li>
          ))}
        </ul>
      </section>

      {/* Social proof */}
      <section className="mt-16">
        <h2 className="text-2xl font-semibold text-zinc-900">
          Что говорят родители и ученики
        </h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {REVIEWS.map((review) => (
            <blockquote
              key={review.author}
              className="chem-card rounded-xl p-4 text-sm text-zinc-700"
            >
              <p>«{review.quote}»</p>
              <footer className="mt-3 text-xs text-zinc-500">— {review.author}</footer>
            </blockquote>
          ))}
        </div>
        <p className="mt-6 text-center text-sm font-medium text-zinc-600">
          8+ лет · 100+ учеников · ЕГЭ и ОГЭ · онлайн
        </p>
      </section>

      {/* Features */}
      <section className="mt-16">
        <h2 className="text-2xl font-semibold text-zinc-900">
          Что будет на бесплатной диагностике
        </h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="chem-card rounded-xl p-5">
              <h3 className="font-semibold text-chem-teal-dark">{feature.title}</h3>
              <p className="mt-2 text-sm text-zinc-600">{feature.text}</p>
            </div>
          ))}
        </div>
        <p className="mt-4 text-center">
          <a href="#form" className="text-sm font-medium text-chem-teal underline">
            Записаться
          </a>
        </p>
      </section>

      {/* Pricing */}
      <section className="mt-16">
        <h2 className="text-2xl font-semibold text-zinc-900">Форматы занятий</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="chem-card rounded-xl p-6">
            <h3 className="text-lg font-semibold text-zinc-900">Индивидуально</h3>
            <p className="mt-2 text-3xl font-semibold text-chem-teal-dark">
              2&nbsp;500&nbsp;₽ <span className="text-base font-normal text-zinc-600">/ час</span>
            </p>
            <p className="mt-3 text-sm text-zinc-600">
              Максимум внимания, подходит при сложном старте или нестандартном графике.
            </p>
            <a href="#form" className="chem-btn-primary mt-4 inline-block px-4 py-2 text-sm">
              Записаться
            </a>
          </div>
          <div className="chem-card rounded-xl p-6">
            <h3 className="text-lg font-semibold text-zinc-900">Группа 4–6 человек</h3>
            <p className="mt-2 text-3xl font-semibold text-chem-teal-dark">
              1&nbsp;500&nbsp;₽{" "}
              <span className="text-base font-normal text-zinc-600">/ чел. за 2 ч</span>
            </p>
            <p className="mt-3 text-sm text-zinc-600">
              Дисциплина группы и доступнее по цене. Старт набора — с 1 сентября.
            </p>
            <a href="#form" className="chem-btn-primary mt-4 inline-block px-4 py-2 text-sm">
              Записаться
            </a>
          </div>
        </div>
        <p className="mt-4 text-center text-sm text-zinc-600">
          Платформа включена в подготовку — отдельно не продаётся. Первый шаг — бесплатная
          диагностика.
        </p>
      </section>

      {/* About */}
      <section className="mt-16">
        <div className="grid gap-8 sm:grid-cols-[minmax(0,12rem)_1fr] sm:items-start">
          <Image
            src={TEACHER_PORTRAIT}
            alt="Роман Алексеевич"
            width={742}
            height={1024}
            className="mx-auto h-auto w-48 rounded-2xl object-cover shadow-md ring-2 ring-chem-teal/15 sm:mx-0 sm:w-full"
            sizes="(max-width: 640px) 192px, 12rem"
          />
          <div>
            <h2 className="text-2xl font-semibold text-zinc-900">Роман Алексеевич</h2>
            <p className="mt-4 text-zinc-600">
              Преподаю химию онлайн 8 лет — индивидуально и в группах. Готовлю к ЕГЭ и ОГЭ: от
              базы до заданий 27–34. Собственная программа на весь учебный год и платформа для
              учеников — не разрозненные файлы в Telegram.
            </p>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="mt-16">
        <h2 className="text-2xl font-semibold text-zinc-900">Частые вопросы</h2>
        <div className="mt-6">
          <FaqAccordion items={[...FAQ_ITEMS]} />
        </div>
      </section>

      {/* Final CTA */}
      <section className="mt-16 rounded-xl bg-chem-teal px-6 py-10 text-white sm:px-10">
        <h2 className="text-2xl font-semibold">
          Запишитесь на диагностику — 30 минут, бесплатно
        </h2>
        <p className="mt-2 text-white/90">
          Оставьте заявку — перезвоним в течение 2 часов в рабочее время.
        </p>
        <div className="mt-6 max-w-md [&_.chem-card]:border-0">
          <LeadFormSection
            sourcePage="/zapis"
            formId="footer-form"
            showSocialLinks={false}
          />
        </div>
      </section>
    </div>
  );
}
