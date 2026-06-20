import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { HomeworkForm } from "@/components/homework/HomeworkForm";
import {
  getStudents,
  getTeacherThemesWithTaskCounts,
  getTeacherThemeTasks,
  getTestVariants,
  getTextbookTopics,
} from "@/lib/api/server";

export default async function TeacherHomeworkNewPage() {
  const [students, topics, egeVariants, ogeVariants, themeSummaries] =
    await Promise.all([
      getStudents(),
      getTextbookTopics(),
      getTestVariants("ege"),
      getTestVariants("oge"),
      getTeacherThemesWithTaskCounts(),
    ]);

  const teacherThemes = await Promise.all(
    themeSummaries.map(async (theme) => ({
      id: theme.id,
      title: theme.title,
      tasks: await getTeacherThemeTasks(theme.id),
    })),
  );

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Кабинет преподавателя</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            Новое домашнее задание
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/teacher/homework" className="chem-link text-sm">
            К списку
          </Link>
          <LogoutButton />
        </div>
      </div>

      <section className="mt-10">
        <HomeworkForm
          students={students}
          topics={topics.map((topic) => topic.topic)}
          variantsByTrack={{
            ege: egeVariants.map((variant) => variant.filename),
            oge: ogeVariants.map((variant) => variant.filename),
          }}
          teacherThemes={teacherThemes}
        />
      </section>
    </main>
  );
}
