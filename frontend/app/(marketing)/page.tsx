import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Химыч — репетитор по химии ЕГЭ и ОГЭ онлайн",
  description:
    "Онлайн-подготовка к ЕГЭ и ОГЭ по химии с личной платформой. Бесплатная диагностика 30 минут.",
  alternates: { canonical: "/" },
};

const HIGHLIGHTS = [
  "8 лет опыта — индивидуально и в группах 4–6 человек",
  "Платформа с учебником, тестами и домашними заданиями между уроками",
  "Программа на весь учебный год, а не хаотичные темы",
] as const;

export default function MarketingHomePage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-24">
      <p className="chem-kicker">Репетитор по химии</p>
      <h1 className="mt-2 text-4xl font-semibold text-zinc-900 sm:text-5xl">
        Химыч — подготовка к ЕГЭ и ОГЭ онлайн
      </h1>
      <p className="mt-6 text-lg text-zinc-600">
        Роман Алексеевич — репетитор по химии с собственной платформой для учеников. Помогаю
        системно готовиться к экзаменам: от диагностики уровня до заданий 27–34.
      </p>

      <ul className="mt-8 space-y-3">
        {HIGHLIGHTS.map((item) => (
          <li key={item} className="flex gap-3 text-zinc-700">
            <span className="text-chem-teal" aria-hidden="true">
              ✓
            </span>
            {item}
          </li>
        ))}
      </ul>

      <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
        <Link href="/zapis" className="chem-btn-primary px-6 py-3 text-center text-base">
          Записаться на диагностику
        </Link>
        <Link
          href="/ceny"
          className="rounded-md border border-chem-teal/30 bg-chem-card px-6 py-3 text-center text-base font-medium text-chem-teal-dark hover:bg-chem-teal-soft/30"
        >
          Цены
        </Link>
        <Link
          href="/blog"
          className="rounded-md border border-zinc-200 bg-chem-card px-6 py-3 text-center text-base font-medium text-zinc-700 hover:bg-zinc-50"
        >
          Блог
        </Link>
      </div>
    </div>
  );
}
