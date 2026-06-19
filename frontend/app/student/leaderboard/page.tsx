import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { LeaderboardTable } from "@/components/student/LeaderboardTable";
import { DecorativeBlobs } from "@/components/ui/DecorativeBlobs";
import { getCurrentUser } from "@/lib/api/server";

export default async function StudentLeaderboardPage() {
  const user = await getCurrentUser();

  return (
    <main className="relative isolate mx-auto max-w-3xl min-w-0 px-4 py-8 sm:px-6 sm:py-12">
      <DecorativeBlobs scoped />

      <div className="relative z-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="chem-kicker">Кабинет ученика</p>
            <h1 className="mt-1 text-2xl font-semibold text-zinc-900">Рейтинг</h1>
            <p className="mt-1 text-sm text-zinc-600">{user?.email}</p>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/student" className="chem-link text-sm">
              На главную
            </Link>
            <LogoutButton />
          </div>
        </div>

        <section className="mt-8 sm:mt-10" aria-labelledby="leaderboard-page-heading">
          <h2 id="leaderboard-page-heading" className="sr-only">
            Таблица рейтинга учеников
          </h2>
          <LeaderboardTable />
        </section>
      </div>
    </main>
  );
}
