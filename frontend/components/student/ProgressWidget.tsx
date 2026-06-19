"use client";

import { useEffect, useState } from "react";

import { formatFetchError } from "@/lib/api/client";
import { getMyStats } from "@/lib/api/activity";
import type { StudentStats } from "@/lib/api/types";
import { formatTotalMinutes } from "@/lib/format-duration";

export function ProgressWidget({
  initialStats,
}: {
  initialStats?: StudentStats | null;
}) {
  const [stats, setStats] = useState<StudentStats | null>(initialStats ?? null);
  const [loading, setLoading] = useState(initialStats === undefined);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialStats !== undefined) {
      return;
    }

    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getMyStats();
        if (!cancelled) {
          setStats(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(formatFetchError(err, "Не удалось загрузить прогресс"));
          setStats(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [initialStats]);

  if (loading) {
    return (
      <section
        aria-labelledby="progress-widget-heading"
        className="chem-card rounded-xl p-4 sm:p-5"
      >
        <h2 id="progress-widget-heading" className="chem-kicker">
          Мой прогресс
        </h2>
        <p className="mt-3 text-sm text-zinc-500" aria-live="polite">
          Загрузка…
        </p>
      </section>
    );
  }

  if (error || !stats) {
    return (
      <section
        aria-labelledby="progress-widget-heading"
        className="chem-card rounded-xl p-4 sm:p-5"
      >
        <h2 id="progress-widget-heading" className="chem-kicker">
          Мой прогресс
        </h2>
        <p className="mt-3 text-sm text-text-negative" role="alert">
          {error ?? "Данные недоступны"}
        </p>
      </section>
    );
  }

  return (
    <section
      aria-labelledby="progress-widget-heading"
      className="chem-card overflow-hidden rounded-xl"
    >
      <div className="bg-chem-teal px-4 py-3 sm:px-5">
        <h2 id="progress-widget-heading" className="text-base font-semibold text-white">
          Мой прогресс
        </h2>
      </div>

      <div className="grid grid-cols-2 gap-4 px-4 py-4 sm:grid-cols-4 sm:px-5 sm:py-5">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
            За неделю
          </p>
          <p className="mt-1 text-2xl font-semibold text-chem-teal-dark">
            {stats.week_points}
          </p>
          <p className="mt-0.5 text-xs text-zinc-500">баллов</p>
        </div>

        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
            Всего
          </p>
          <p className="mt-1 text-2xl font-semibold text-chem-teal-dark">
            {stats.total_points}
          </p>
          <p className="mt-0.5 text-xs text-zinc-500">баллов</p>
        </div>

        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
            Серия
          </p>
          <p className="mt-1 text-2xl font-semibold text-chem-teal-dark">
            {stats.current_streak}
          </p>
          <p className="mt-0.5 text-xs text-zinc-500">
            {stats.current_streak === 1
              ? "день"
              : stats.current_streak >= 2 && stats.current_streak <= 4
                ? "дня"
                : "дней"}
            {stats.longest_streak > stats.current_streak
              ? ` · рекорд ${stats.longest_streak}`
              : null}
          </p>
        </div>

        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
            Активность
          </p>
          <p className="mt-1 text-lg font-semibold text-chem-teal-dark">
            {stats.tasks_solved}{" "}
            <span className="text-sm font-medium text-zinc-600">
              {stats.tasks_solved === 1
                ? "задача"
                : stats.tasks_solved >= 2 && stats.tasks_solved <= 4
                  ? "задачи"
                  : "задач"}
            </span>
          </p>
          <p className="mt-0.5 text-xs text-zinc-500">
            {formatTotalMinutes(stats.total_minutes)} в тестах
          </p>
        </div>
      </div>
    </section>
  );
}
