import Link from "next/link";

import { TemplateList } from "@/components/homework/TemplateList";
import { getCurrentUser, getHomeworkTemplates } from "@/lib/api/server";

export default async function TeacherHomeworkPage() {
  const [user, templates] = await Promise.all([
    getCurrentUser(),
    getHomeworkTemplates(),
  ]);

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Кабинет преподавателя</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">Задания</h1>
          <p className="mt-1 text-sm text-zinc-600">{user?.email}</p>
        </div>
        <Link href="/teacher" className="chem-link shrink-0 text-sm">
          На главную
        </Link>
      </div>

      <div className="mt-6">
        <Link
          href="/teacher/homework/new"
          className="chem-btn-primary inline-flex px-4 py-2 text-sm"
        >
          Новый шаблон
        </Link>
      </div>

      <section className="mt-8">
        <TemplateList templates={templates} />
      </section>
    </main>
  );
}
