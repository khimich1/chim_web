import Link from "next/link";

import { ThemesList } from "@/components/teacher/ThemesList";
import { getCurrentUser, getTeacherThemes } from "@/lib/api/server";

export default async function TeacherThemesPage() {
  const [user, themes] = await Promise.all([getCurrentUser(), getTeacherThemes()]);

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Кабинет преподавателя</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            Конструктор тем
          </h1>
          <p className="mt-1 text-sm text-zinc-600">{user?.email}</p>
        </div>
        <Link href="/teacher" className="chem-link shrink-0 text-sm">
          На главную
        </Link>
      </div>

      <section className="mt-10">
        <ThemesList themes={themes} />
      </section>
    </main>
  );
}
