"use client";

import { useCallback, useEffect, useState } from "react";

import { formatFetchError } from "@/lib/api/client";
import {
  getLeaderboard,
  getMyStats,
  type LeaderboardPeriod,
} from "@/lib/api/activity";
import type { LeaderboardEntry } from "@/lib/api/types";
import { resolvePublicDisplayName } from "@/lib/activity/display-name";

const PERIOD_OPTIONS: { value: LeaderboardPeriod; label: string }[] = [
  { value: "week", label: "За неделю" },
  { value: "all_time", label: "За всё время" },
];

function pointsLabel(points: number): string {
  const mod10 = points % 10;
  const mod100 = points % 100;
  if (mod10 === 1 && mod100 !== 11) {
    return "балл";
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return "балла";
  }
  return "баллов";
}

function isCurrentStudentRow(
  entry: LeaderboardEntry,
  currentLabel: string | null,
): boolean {
  return currentLabel !== null && entry.display_name === currentLabel;
}

export function LeaderboardTable({
  currentDisplayName,
  currentStudentId: currentStudentIdProp,
}: {
  currentDisplayName?: string | null;
  currentStudentId?: string;
} = {}) {
  const [period, setPeriod] = useState<LeaderboardPeriod>("week");
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [currentStudentId, setCurrentStudentId] = useState<string | null>(
    currentStudentIdProp ?? null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const currentLabel =
    currentDisplayName !== undefined
      ? currentDisplayName
        ? resolvePublicDisplayName(currentDisplayName, currentStudentId ?? "")
        : currentStudentId
          ? resolvePublicDisplayName(null, currentStudentId)
          : null
      : currentStudentId
        ? resolvePublicDisplayName(null, currentStudentId)
        : null;

  const loadLeaderboard = useCallback(async (nextPeriod: LeaderboardPeriod) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getLeaderboard(nextPeriod);
      setEntries(data);
    } catch (err) {
      setError(formatFetchError(err, "Не удалось загрузить рейтинг"));
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (currentStudentIdProp !== undefined) {
      setCurrentStudentId(currentStudentIdProp);
      return;
    }

    let cancelled = false;

    async function loadStudentId() {
      try {
        const stats = await getMyStats();
        if (!cancelled) {
          setCurrentStudentId(stats.student_id);
        }
      } catch {
        if (!cancelled) {
          setCurrentStudentId(null);
        }
      }
    }

    void loadStudentId();
    return () => {
      cancelled = true;
    };
  }, [currentStudentIdProp]);

  useEffect(() => {
    void loadLeaderboard(period);
  }, [loadLeaderboard, period]);

  function handlePeriodChange(nextPeriod: LeaderboardPeriod) {
    if (nextPeriod === period) {
      return;
    }
    setPeriod(nextPeriod);
  }

  return (
    <section
      aria-labelledby="leaderboard-heading"
      className="chem-card overflow-hidden rounded-xl"
    >
      <div className="bg-chem-teal px-4 py-3 sm:px-5">
        <h2 id="leaderboard-heading" className="text-base font-semibold text-white">
          Рейтинг
        </h2>
      </div>

      <div className="space-y-4 px-4 py-4 sm:px-5 sm:py-5">
        <div
          role="group"
          aria-label="Период рейтинга"
          className="flex flex-wrap gap-2"
        >
          {PERIOD_OPTIONS.map(({ value, label }) => {
            const active = period === value;
            return (
              <button
                key={value}
                type="button"
                aria-pressed={active}
                onClick={() => handlePeriodChange(value)}
                className={`min-h-[44px] rounded-md px-4 py-2 text-sm font-medium transition ${
                  active
                    ? "bg-chem-teal text-white shadow-sm"
                    : "border border-chem-teal/30 bg-white text-chem-teal hover:bg-chem-teal-soft/50"
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>

        {loading ? (
          <p className="text-sm text-zinc-500" aria-live="polite">
            Загрузка…
          </p>
        ) : error ? (
          <p className="text-sm text-text-negative" role="alert">
            {error}
          </p>
        ) : entries.length === 0 ? (
          <p className="text-sm text-zinc-500" aria-live="polite">
            Пока нет участников в рейтинге.
          </p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-zinc-200">
            <div
              className="hidden grid-cols-[4rem_1fr_auto] gap-3 px-3 py-3 text-sm font-medium chem-table-head sm:grid"
              aria-hidden="true"
            >
              <span>Место</span>
              <span>Ученик</span>
              <span className="text-right">Баллы</span>
            </div>

            <ul className="divide-y divide-zinc-200" aria-label="Рейтинг учеников">
              {entries.map((entry) => {
                const isCurrent = isCurrentStudentRow(entry, currentLabel);
                return (
                  <li
                    key={`${entry.rank}-${entry.display_name}`}
                    className={`grid grid-cols-1 gap-2 px-4 py-3 sm:grid-cols-[4rem_1fr_auto] sm:items-center sm:gap-3 sm:px-3 ${
                      isCurrent
                        ? "bg-chem-teal-soft/70 ring-1 ring-inset ring-chem-teal/25"
                        : "bg-white"
                    }`}
                    aria-current={isCurrent ? "true" : undefined}
                  >
                    <p className="text-xs font-semibold uppercase tracking-wide text-chem-teal-dark sm:text-sm sm:normal-case sm:tracking-normal">
                      <span className="sm:hidden">Место </span>
                      {entry.rank}
                    </p>
                    <p className="text-base font-semibold text-zinc-900 sm:text-sm sm:font-medium">
                      {entry.display_name}
                      {isCurrent ? (
                        <span className="ml-2 text-xs font-medium text-chem-teal-dark">
                          (вы)
                        </span>
                      ) : null}
                    </p>
                    <p className="text-base font-semibold text-zinc-900 sm:text-right sm:text-sm">
                      {entry.points}{" "}
                      <span className="font-normal text-zinc-500">
                        {pointsLabel(entry.points)}
                      </span>
                    </p>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}
