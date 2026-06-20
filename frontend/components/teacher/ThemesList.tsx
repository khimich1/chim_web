"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError } from "@/lib/api/client";
import { createTeacherTheme } from "@/lib/api/teacher-themes";

export interface ThemeListItem {
  id: string;
  title: string;
  is_published: boolean;
  task_count: number;
}

export function ThemesList({ themes }: { themes: ThemeListItem[] }) {
  const router = useRouter();
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate() {
    setError(null);
    setCreating(true);
    try {
      const theme = await createTeacherTheme({
        title: "Новая тема",
        is_published: false,
      });
      router.push(`/teacher/themes/${theme.id}`);
    } catch (err) {
      setCreating(false);
      setError(
        err instanceof ApiError ? err.message : "Не удалось создать тему.",
      );
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => void handleCreate()}
          disabled={creating}
          className="chem-btn-primary px-4 py-2 text-sm disabled:opacity-60"
        >
          {creating ? "Создание…" : "Создать тему"}
        </button>
      </div>

      {error ? (
        <p role="alert" className="text-sm text-[var(--chem-crimson)]">
          {error}
        </p>
      ) : null}

      {themes.length === 0 ? (
        <p className="text-sm text-zinc-500">
          Тем пока нет. Создайте первую тему с заданиями.
        </p>
      ) : (
        <ul className="chem-card divide-y divide-zinc-200 overflow-hidden rounded-xl">
          {themes.map((theme) => (
            <li key={theme.id}>
              <Link
                href={`/teacher/themes/${theme.id}`}
                className="flex items-center justify-between gap-3 px-4 py-3.5 transition hover:bg-zinc-50 sm:px-5"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium text-zinc-900">
                    {theme.title}
                  </p>
                  <p className="text-xs text-zinc-500">
                    {theme.task_count}{" "}
                    {theme.task_count === 1
                      ? "задание"
                      : theme.task_count < 5
                        ? "задания"
                        : "заданий"}
                  </p>
                </div>
                <span
                  className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${
                    theme.is_published
                      ? "bg-chem-teal-soft text-chem-teal-dark"
                      : "bg-zinc-100 text-zinc-500"
                  }`}
                >
                  {theme.is_published ? "Опубликована" : "Черновик"}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
