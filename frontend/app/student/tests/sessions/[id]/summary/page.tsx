import Link from "next/link";
import { notFound } from "next/navigation";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { HomeworkSubmitButton } from "@/components/homework/HomeworkSubmitButton";
import { SessionSummary } from "@/components/tests/SessionSummary";
import { getTestSession } from "@/lib/api/server";

export default async function TestSessionSummaryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const session = await getTestSession(id);

  if (!session) {
    notFound();
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Тест завершён</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">Итоги</h1>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/student/tests" className="chem-link text-sm">
            К тестам
          </Link>
          <LogoutButton />
        </div>
      </div>

      <section className="mt-10">
        <SessionSummary session={session} />
      </section>

      {session.homework_assignment_id && session.status === "completed" ? (
        <section className="chem-card mt-8 rounded-lg p-6">
          <HomeworkSubmitButton
            homeworkId={session.homework_assignment_id}
            sessionId={session.id}
          />
        </section>
      ) : null}
    </main>
  );
}
