"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { BrandLogo } from "@/components/ui/BrandLogo";

const NAV_LINKS = [
  { href: "/student", label: "Главная", exact: true },
  { href: "/student/textbook", label: "Учебник", exact: false },
  { href: "/student/tests", label: "Тесты", exact: false },
  { href: "/student/homework", label: "Задания", exact: false },
] as const;

function linkIsActive(pathname: string, href: string, exact: boolean): boolean {
  if (exact) {
    return pathname === href;
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function StudentNav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-30 border-b border-zinc-200/80 bg-white/90 backdrop-blur-sm">
      <div className="mx-auto flex max-w-5xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <Link href="/student" className="inline-flex min-h-[44px] items-center">
          <BrandLogo size={28} />
        </Link>

        <nav aria-label="Разделы кабинета ученика">
          <ul className="flex flex-wrap gap-1.5 sm:gap-2">
            {NAV_LINKS.map(({ href, label, exact }) => {
              const active = linkIsActive(pathname, href, exact);
              return (
                <li key={href}>
                  <Link
                    href={href}
                    aria-current={active ? "page" : undefined}
                    className={`inline-flex min-h-[44px] items-center rounded-md px-3 py-2 text-sm font-medium transition ${
                      active
                        ? "chem-nav-active"
                        : "text-zinc-700 hover:bg-chem-teal-soft/50 hover:text-chem-teal-dark"
                    }`}
                  >
                    {label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </header>
  );
}
