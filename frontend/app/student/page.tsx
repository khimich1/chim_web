import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { TrackBadge } from "@/components/ui/TrackBadge";
import { getCurrentUser, getHomeworkList } from "@/lib/api/server";

export default async function StudentDashboard() {
  const [user, homework] = await Promise.all([
    getCurrentUser(),
    getHomeworkList(),
  ]);

  const activeHomework = homework.filter(
    (item) => item.status === "assigned" || item.status === "in_progress",
  ).length;

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
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

      {activeHomework > 0 ? (
        <p className="mt-6 text-sm text-zinc-600">
          Активных заданий: {activeHomework}
        </p>
      ) : null}

      <div className="mt-8 flex flex-wrap gap-3">
        <Link
          href="/student/homework"
          className="chem-btn-primary inline-flex px-4 py-2 text-sm"
        >
          Мои задания
        </Link>
        <Link
          href="/student/textbook"
          className="inline-flex rounded-md border border-chem-royal px-4 py-2 text-sm font-medium text-chem-royal transition hover:bg-chem-royal/5"
        >
          Учебник
        </Link>
        <Link
          href="/student/tests"
          className="inline-flex rounded-md border border-chem-royal px-4 py-2 text-sm font-medium text-chem-royal transition hover:bg-chem-royal/5"
        >
          Тесты
        </Link>
      </div>
    </main>
  );
}
