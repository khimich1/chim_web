import Link from "next/link";

import { BrandLogo } from "@/components/ui/BrandLogo";

const NAV_LINKS = [
  { href: "/zapis", label: "Запись" },
  { href: "/ceny", label: "Цены" },
  { href: "/blog", label: "Блог" },
] as const;

export function MarketingHeader() {
  return (
    <header className="border-b border-chem-teal/10 bg-chem-card/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
        <Link href="/" className="shrink-0 rounded-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-chem-teal">
          <BrandLogo size={32} label="Химыч" />
        </Link>
        <nav aria-label="Основная навигация" className="hidden items-center gap-6 sm:flex">
          {NAV_LINKS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-sm font-medium text-zinc-700 hover:text-chem-teal-dark"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <Link
          href="/login"
          className="text-sm text-zinc-500 hover:text-chem-teal-dark"
        >
          Вход для учеников
        </Link>
      </div>
    </header>
  );
}
