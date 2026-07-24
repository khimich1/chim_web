"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { NotificationBell } from "@/components/notifications/NotificationBell";
import { BrandLogo } from "@/components/ui/BrandLogo";
import type { Notification } from "@/lib/api/types";

const NAV_LINKS = [
  { href: "/teacher", label: "Главная", exact: true },
  { href: "/teacher/students", label: "Ученики", exact: false },
  { href: "/teacher/themes", label: "Темы", exact: false },
  { href: "/teacher/homework", label: "Задания", exact: false },
  { href: "/teacher/notifications", label: "Уведомления", exact: false },
] as const;

function linkIsActive(pathname: string, href: string, exact: boolean): boolean {
  if (exact) {
    return pathname === href;
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function TeacherNav({
  initialNotifications,
  initialUnread,
}: {
  initialNotifications: Notification[];
  initialUnread: number;
}) {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-30 border-b border-zinc-200/80 bg-white/90 backdrop-blur-sm">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-4 gap-y-3 px-4 py-3 sm:px-6">
        <div className="flex min-w-0 flex-1 items-center">
          <Link href="/teacher" className="inline-flex min-h-[44px] items-center">
            <BrandLogo size={28} />
          </Link>
        </div>

        <nav
          aria-label="Разделы кабинета преподавателя"
          className="order-3 w-full sm:order-none sm:w-auto"
        >
          <ul className="flex flex-wrap justify-center gap-1.5 sm:gap-2">
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

        <div className="flex flex-1 items-center justify-end gap-2">
          <NotificationBell
            initialNotifications={initialNotifications}
            initialUnread={initialUnread}
          />
          <LogoutButton />
        </div>
      </div>
    </header>
  );
}
