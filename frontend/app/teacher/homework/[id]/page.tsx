import Link from "next/link";
import { notFound } from "next/navigation";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { formatHomeworkItemLabel } from "@/components/homework/homework-utils";
import { getHomework } from "@/lib/api/server";

export default async function TeacherHomeworkDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const homework = await getHomework(id);

  if (!homework) {
    notFound();
  }

  const progressByIndex = new Map(
    homework.progress.map((row) => [row.item_index, row.completed]),
  );

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Домашнее задание</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            {homework.title}
          </h1>
          <p className="mt-1 text-sm text-zinc-600">
            {homework.student_email}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/teacher/homework" className="chem-link text-sm">
            К списку
          </Link>
          <LogoutButton />
        </div>
      </div>

      <section className="chem-card mt-10 rounded-lg p-6">
        {homework.description ? (
          <p className="text-sm text-zinc-600">{homework.description}</p>
        ) : null}
        <dl className="mt-4 grid gap-3 text-sm">
          <div>
            <dt className="font-medium text-zinc-700">Статус</dt>
            <dd className="text-zinc-900">{homework.status}</dd>
          </div>
          {homework.submission ? (
            <div>
              <dt className="font-medium text-zinc-700">Результат</dt>
              <dd className="text-zinc-900">
                {homework.submission.score != null
                  ? `${homework.submission.score} / ${homework.submission.max_score}`
                  : "Сдано (лекции)"}
              </dd>
            </div>
          ) : null}
        </dl>

        <div className="mt-6 border-t border-zinc-200 pt-4">
          <h2 className="text-sm font-medium text-zinc-700">
            Пункты ({homework.items.length})
          </h2>
          <ol className="mt-3 flex flex-col gap-2">
            {homework.items.map((item, index) => (
              <li
                key={`${item.kind}-${index}`}
                className="flex flex-wrap items-center justify-between gap-2 text-sm"
              >
                <span>
                  {index + 1}. {formatHomeworkItemLabel(item)}
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    progressByIndex.get(index)
                      ? "bg-chem-green/10 text-chem-green"
                      : "bg-zinc-100 text-zinc-600"
                  }`}
                >
                  {progressByIndex.get(index) ? "Выполнено" : "Не выполнено"}
                </span>
              </li>
            ))}
          </ol>
        </div>
      </section>
    </main>
  );
}
