import Link from "next/link";

import { StudentsHub } from "@/components/students/StudentsHub";
import {
  getCurrentUser,
  getHomeworkTemplates,
  getStudents,
  getTeacherStudentsStats,
} from "@/lib/api/server";

export default async function StudentsPage() {
  const [user, students, stats, templates] = await Promise.all([
    getCurrentUser(),
    getStudents(),
    getTeacherStudentsStats(),
    getHomeworkTemplates(),
  ]);

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Кабинет преподавателя</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">Ученики</h1>
          <p className="mt-1 text-sm text-zinc-600">{user?.email}</p>
        </div>
        <Link href="/teacher" className="chem-link shrink-0 text-sm">
          На главную
        </Link>
      </div>

      <StudentsHub students={students} stats={stats} templates={templates} />
    </main>
  );
}
