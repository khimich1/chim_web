import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { getCurrentUser } from "@/lib/api/server";

export default async function TeacherDashboard() {
  const user = await getCurrentUser();

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Кабинет преподавателя</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            {user?.email}
          </h1>
        </div>
        <LogoutButton />
      </div>

      <div className="mt-8 flex flex-col gap-4">
        <p className="text-zinc-600">
          Домашние задания и уведомления появятся в следующих версиях.
        </p>
        <Link href="/teacher/students" className="chem-btn-primary inline-flex w-fit px-4 py-2 text-sm">
          Ученики
        </Link>
      </div>
    </main>
  );
}
