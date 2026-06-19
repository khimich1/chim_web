import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { OnboardingChecklist } from "@/components/student/OnboardingChecklist";
import { ProgressWidget } from "@/components/student/ProgressWidget";
import { ResumeSessionCards } from "@/components/student/ResumeSessionCards";
import { TrackBadge } from "@/components/ui/TrackBadge";
import { DecorativeBlobs } from "@/components/ui/DecorativeBlobs";
import { getCurrentUser, getHomeworkList, getOnboardingStatus, getTestVariants } from "@/lib/api/server";

const QUICK_LINKS = [
  {
    href: "/student/homework",
    title: "Мои задания",
    description: "Домашние задания от преподавателя",
    statKey: "homework" as const,
  },
  {
    href: "/student/textbook",
    title: "Учебник",
    description: "Лекции по темам с аудио",
    statKey: null,
  },
  {
    href: "/student/tests",
    title: "Тесты",
    description: "Пошаговое прохождение вариантов",
    statKey: null,
  },
  {
    href: "/student/leaderboard",
    title: "Рейтинг",
    description: "Топ учеников за неделю и за всё время",
    statKey: null,
  },
];

export default async function StudentDashboard() {
  const [user, homework, variants, onboarding] = await Promise.all([
    getCurrentUser(),
    getHomeworkList(),
    getTestVariants(),
    getOnboardingStatus(),
  ]);

  const activeHomework = homework.filter(
    (item) => item.status === "assigned" || item.status === "in_progress",
  ).length;

  return (
    <main className="relative isolate mx-auto max-w-3xl min-w-0 px-4 py-8 sm:px-6 sm:py-12">
      <DecorativeBlobs scoped />

      <div className="relative z-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="chem-kicker">Кабинет ученика</p>
            <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
              {user?.email}
            </h1>
            {user?.track ? (
              <p className="mt-2">
                <TrackBadge track={user.track} />
              </p>
            ) : null}
          </div>
          <LogoutButton />
        </div>

        <div className="mt-8 space-y-8 sm:mt-10">
          {onboarding ? (
            <OnboardingChecklist checklist={onboarding.checklist} />
          ) : null}
          <ProgressWidget />
          <ResumeSessionCards homework={homework} variants={variants} />
        </div>

        <section aria-labelledby="dashboard-quick-links" className="mt-8 sm:mt-10">
          <h2 id="dashboard-quick-links" className="sr-only">
            Быстрые ссылки
          </h2>
          <ul className="flex flex-col gap-4">
            {QUICK_LINKS.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="chem-card group block overflow-hidden rounded-xl transition hover:shadow-md"
                >
                  <div className="bg-chem-teal px-4 py-3 sm:px-5">
                    <h3 className="text-base font-semibold text-white">
                      {item.title}
                    </h3>
                  </div>
                  <div className="px-4 py-4 sm:px-5">
                    <p className="text-sm text-zinc-600">{item.description}</p>
                    {item.statKey === "homework" && activeHomework > 0 ? (
                      <p
                        className="mt-2 text-sm font-medium text-chem-teal-dark"
                        aria-live="polite"
                      >
                        Активных заданий: {activeHomework}
                      </p>
                    ) : null}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
