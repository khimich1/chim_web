import Link from "next/link";

import { HomeworkForm } from "@/components/homework/HomeworkForm";
import {
  getTeacherThemes,
  getTeacherThemeTasks,
  getTestVariants,
  getTextbookTopics,
} from "@/lib/api/server";

export default async function TeacherHomeworkNewPage() {
  const [topics, egeVariants, ogeVariants, themes] = await Promise.all([
    getTextbookTopics(),
    getTestVariants("ege"),
    getTestVariants("oge"),
    getTeacherThemes(),
  ]);

  const teacherThemes = await Promise.all(
    themes.map(async (theme) => ({
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
            Новый шаблон задания
          </h1>
        </div>
        <Link href="/teacher/homework" className="chem-link shrink-0 text-sm">
          К списку
        </Link>
      </div>

      <section className="mt-10">
        <HomeworkForm
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
