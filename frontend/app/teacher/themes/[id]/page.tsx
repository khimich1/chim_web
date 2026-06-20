import Link from "next/link";
import { notFound } from "next/navigation";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { ThemeDetailView } from "@/components/teacher/ThemeDetailView";
import {
  getCurrentUser,
  getTeacherTheme,
  getTeacherThemeTasks,
} from "@/lib/api/server";

export default async function TeacherThemeDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [user, theme, tasks] = await Promise.all([
    getCurrentUser(),
    getTeacherTheme(id),
    getTeacherThemeTasks(id),
  ]);

  if (!theme) {
    notFound();
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Конструктор тем</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            {theme.title}
          </h1>
          <p className="mt-1 text-sm text-zinc-600">{user?.email}</p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/teacher/themes" className="chem-link text-sm">
            К списку тем
          </Link>
          <LogoutButton />
        </div>
      </div>

      <section className="mt-10">
        <ThemeDetailView initialTheme={theme} initialTasks={tasks} />
      </section>
    </main>
  );
}
