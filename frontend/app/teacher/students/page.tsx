import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { CreateStudentForm } from "@/components/students/CreateStudentForm";
import { StudentList } from "@/components/students/StudentList";
import { getCurrentUser, getStudents, getTeacherStudentsStats } from "@/lib/api/server";

export default async function StudentsPage() {
  const [user, students, stats] = await Promise.all([
    getCurrentUser(),
    getStudents(),
    getTeacherStudentsStats(),
  ]);

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Кабинет преподавателя</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">Ученики</h1>
          <p className="mt-1 text-sm text-zinc-600">{user?.email}</p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/teacher" className="chem-link text-sm">
            На главную
          </Link>
          <LogoutButton />
        </div>
      </div>

      <section className="mt-10">
        <CreateStudentForm />
      </section>

      <section className="mt-10">
        <h2 className="mb-4 text-lg font-semibold text-zinc-900">
          Список ({students.length})
        </h2>
        <StudentList students={students} stats={stats} />
      </section>
    </main>
  );
}
