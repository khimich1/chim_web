import { LogoutButton } from "@/components/auth/LogoutButton";
import { getCurrentUser } from "@/lib/api/server";

export default async function TeacherDashboard() {
  const user = await getCurrentUser();

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">
            Кабинет преподавателя
          </p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            {user?.email}
          </h1>
        </div>
        <LogoutButton />
      </div>

      <p className="mt-8 text-zinc-600">
        Дальше здесь появятся ученики, домашние задания и уведомления.
      </p>
    </main>
  );
}
