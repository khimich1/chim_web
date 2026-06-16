import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { TrackBadge } from "@/components/ui/TrackBadge";
import { getCurrentUser } from "@/lib/api/server";

export default async function StudentDashboard() {
  const user = await getCurrentUser();

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

      <div className="mt-8 flex flex-col gap-4">
        <p className="text-zinc-600">
          Дальше здесь появятся домашние задания.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/student/textbook"
            className="chem-btn-primary inline-flex w-fit px-4 py-2 text-sm"
          >
            Открыть учебник
          </Link>
          <Link
            href="/student/tests"
            className="inline-flex w-fit rounded-md border border-chem-royal px-4 py-2 text-sm font-medium text-chem-royal transition hover:bg-chem-royal/5"
          >
            Перейти к тестам
          </Link>
        </div>
      </div>
    </main>
  );
}
