import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { getCurrentUser, getStudents, listStudentTutorSessions } from "@/lib/api/server";

export default async function TeacherTutorPage() {
  const [user, students] = await Promise.all([getCurrentUser(), getStudents()]);

  const sessionsByStudent = await Promise.all(
    students.map(async (student) => ({
      student,
      sessions: await listStudentTutorSessions(student.id),
    })),
  );

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">AI-советчик</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            Диалоги учеников
          </h1>
          <p className="mt-1 text-sm text-zinc-600">{user?.email}</p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/teacher" className="chem-link text-sm">
            На главную
          </Link>
          <LogoutButton />
        </div>
      </div>

      <div className="mt-10 space-y-8">
        {sessionsByStudent.map(({ student, sessions }) => (
          <section key={student.id}>
            <h2 className="text-lg font-semibold text-zinc-900">
              {student.email}{" "}
              <span className="text-sm font-normal text-zinc-500">
                ({student.track.toUpperCase()})
              </span>
            </h2>
            {sessions.length === 0 ? (
              <p className="mt-2 text-sm text-zinc-500">Сессий пока нет.</p>
            ) : (
              <ul className="mt-3 space-y-2">
                {sessions.map((session) => (
                  <li key={session.id}>
                    <Link
                      href={`/teacher/tutor/${session.id}`}
                      className="chem-link text-sm"
                    >
                      Сессия от{" "}
                      {new Date(session.created_at).toLocaleString("ru-RU")}
                      {session.message_count
                        ? ` · ${session.message_count} сообщ.`
                        : ""}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        ))}
      </div>
    </main>
  );
}
