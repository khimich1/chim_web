import Link from "next/link";
import { notFound } from "next/navigation";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { getCurrentUser, getTutorSessionDetail } from "@/lib/api/server";

export default async function TeacherTutorSessionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [user, session] = await Promise.all([
    getCurrentUser(),
    getTutorSessionDetail(id),
  ]);

  if (!session) {
    notFound();
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">AI-советчик</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            Transcript сессии
          </h1>
          <p className="mt-1 text-sm text-zinc-600">
            {new Date(session.created_at).toLocaleString("ru-RU")}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/teacher/tutor" className="chem-link text-sm">
            К списку
          </Link>
          <LogoutButton />
        </div>
      </div>

      <div className="mt-10 space-y-4">
        {session.messages.map((message) => (
          <article
            key={message.id}
            className={`rounded-lg border px-4 py-3 ${
              message.role === "user"
                ? "border-blue-200 bg-blue-50"
                : "border-zinc-200 bg-white"
            }`}
          >
            <p className="text-xs font-medium text-zinc-500">
              {message.role === "user" ? "Ученик" : "Советчик"} ·{" "}
              {user?.email}
            </p>
            <p className="mt-2 whitespace-pre-wrap text-sm text-zinc-900">
              {message.content}
            </p>
          </article>
        ))}
      </div>
    </main>
  );
}
