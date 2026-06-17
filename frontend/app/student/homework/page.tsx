import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { HomeworkList } from "@/components/homework/HomeworkList";
import { getCurrentUser, getHomeworkList } from "@/lib/api/server";

export default async function StudentHomeworkPage() {
  const [user, homework] = await Promise.all([
    getCurrentUser(),
    getHomeworkList(),
  ]);

  return (
    <main className="mx-auto max-w-3xl min-w-0 px-4 py-8 sm:px-6 sm:py-12">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="chem-kicker">Кабинет ученика</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            Мои задания
          </h1>
          <p className="mt-1 text-sm text-zinc-600">{user?.email}</p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/student" className="chem-link text-sm">
            На главную
          </Link>
          <LogoutButton />
        </div>
      </div>

      <section className="mt-8 sm:mt-10" aria-labelledby="homework-list-heading">
        <h2 id="homework-list-heading" className="sr-only">
          Список домашних заданий
        </h2>
        <HomeworkList assignments={homework} detailBasePath="/student/homework" />
      </section>
    </main>
  );
}
