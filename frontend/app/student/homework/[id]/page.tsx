import Link from "next/link";
import { notFound } from "next/navigation";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { HomeworkItemsPanel } from "@/components/homework/HomeworkItemsPanel";
import { getHomework } from "@/lib/api/server";

export default async function StudentHomeworkDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const homework = await getHomework(id);

  if (!homework) {
    notFound();
  }

  return (
    <main className="mx-auto max-w-3xl min-w-0 px-4 py-8 sm:px-6 sm:py-12">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="chem-kicker">Домашнее задание</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            {homework.title}
          </h1>
          {homework.description ? (
            <p className="mt-2 text-sm text-zinc-600">{homework.description}</p>
          ) : null}
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <Link href="/student/homework" className="chem-link text-sm">
            К списку
          </Link>
          <LogoutButton />
        </div>
      </div>

      <section className="mt-8 sm:mt-10" aria-labelledby="homework-items-heading">
        <h2 id="homework-items-heading" className="sr-only">
          Пункты задания
        </h2>
        <HomeworkItemsPanel homework={homework} />
      </section>
    </main>
  );
}
