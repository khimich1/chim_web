import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { StepView } from "@/components/tests/StepView";
import { formatSessionTitle } from "@/components/tests/session-utils";
import { getTestSession } from "@/lib/api/server";

export default async function TestSessionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const session = await getTestSession(id);

  if (!session) {
    notFound();
  }
  if (session.status === "completed") {
    redirect(`/student/tests/sessions/${id}/summary`);
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Тест</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            {formatSessionTitle(session)}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/student/tests" className="chem-link text-sm">
            К тестам
          </Link>
          <LogoutButton />
        </div>
      </div>

      <section className="mt-10">
        <StepView session={session} />
      </section>
    </main>
  );
}
