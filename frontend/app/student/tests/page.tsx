import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { TestsPicker } from "@/components/tests/TestsPicker";
import {
  getCurrentUser,
  getCustomThemes,
  getTestTaskTypes,
  getTestVariants,
} from "@/lib/api/server";

export default async function TestsPage() {
  const user = await getCurrentUser();
  const track = user?.track ?? "ege";
  const [variants, taskTypes, themes] = await Promise.all([
    getTestVariants(),
    getTestTaskTypes(),
    getCustomThemes(),
  ]);

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Кабинет ученика</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">Тесты</h1>
          <p className="mt-1 text-sm text-zinc-600">
            Выберите вариант, задание по типу или тему преподавателя.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/student" className="chem-link text-sm">
            На главную
          </Link>
          <LogoutButton />
        </div>
      </div>

      <section className="mt-10">
        <TestsPicker
          variants={variants}
          taskTypes={taskTypes}
          themes={themes}
          track={track}
        />
      </section>
    </main>
  );
}
