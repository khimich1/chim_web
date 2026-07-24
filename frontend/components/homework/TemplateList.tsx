"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { deleteHomeworkTemplate } from "@/lib/api/templates";
import { ApiError } from "@/lib/api/client";
import type { HomeworkTemplate } from "@/lib/api/types";

import { homeworkItemsSummary } from "./homework-utils";

export function TemplateList({ templates }: { templates: HomeworkTemplate[] }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleDelete(template: HomeworkTemplate) {
    const confirmed = window.confirm(
      `Удалить шаблон «${template.title}»? Уже выданные задания не изменятся.`,
    );
    if (!confirmed) {
      return;
    }
    setError(null);
    setDeletingId(template.id);
    try {
      await deleteHomeworkTemplate(template.id);
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || "Не удалось удалить шаблон.");
      } else {
        setError("Не удалось удалить шаблон. Попробуйте позже.");
      }
    } finally {
      setDeletingId(null);
    }
  }

  if (templates.length === 0) {
    return (
      <p className="text-sm text-zinc-500" aria-live="polite">
        Шаблонов пока нет. Создайте первый — потом назначайте ученикам.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {error ? (
        <p role="alert" className="text-sm text-[var(--chem-crimson)]">
          {error}
        </p>
      ) : null}
      <ul className="flex min-w-0 flex-col gap-4">
        {templates.map((template) => (
          <li
            key={template.id}
            className="chem-card min-w-0 overflow-hidden rounded-xl"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 bg-chem-teal px-4 py-3 sm:px-5">
              <h2 className="min-w-0 text-base font-semibold">
                <Link
                  href={`/teacher/homework/templates/${template.id}`}
                  className="text-white hover:underline focus-visible:underline"
                >
                  {template.title}
                </Link>
              </h2>
              <button
                type="button"
                onClick={() => handleDelete(template)}
                disabled={deletingId === template.id}
                className="shrink-0 rounded-full bg-white/15 px-2.5 py-0.5 text-xs font-semibold text-white hover:bg-white/25 disabled:opacity-60"
              >
                {deletingId === template.id ? "Удаление…" : "Удалить"}
              </button>
            </div>
            <div className="space-y-1 px-4 py-4 sm:px-5">
              {template.description ? (
                <p className="text-sm text-zinc-600">{template.description}</p>
              ) : null}
              <p className="text-sm text-zinc-700">
                {homeworkItemsSummary(template.items)}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
