"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { createSession, getActiveSession } from "@/lib/api/tests";
import type { CustomThemeListItem } from "@/lib/api/types";

export function ThemePicker({ themes }: { themes: CustomThemeListItem[] }) {
  const router = useRouter();
  const [startingId, setStartingId] = useState<string | null>(null);
  const [activeSessions, setActiveSessions] = useState<Record<string, string>>(
    {},
  );
  const [loadingActive, setLoadingActive] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadActiveSessions() {
      setLoadingActive(true);
      try {
        const entries = await Promise.all(
          themes.map(async (theme) => {
            const result = await getActiveSession({
              customThemeId: theme.id,
            });
            return [theme.id, result.session_id] as const;
          }),
        );
        if (!cancelled) {
          const map: Record<string, string> = {};
          for (const [themeId, sessionId] of entries) {
            if (sessionId) {
              map[themeId] = sessionId;
            }
          }
          setActiveSessions(map);
        }
      } catch {
        if (!cancelled) {
          setActiveSessions({});
        }
      } finally {
        if (!cancelled) {
          setLoadingActive(false);
        }
      }
    }

    void loadActiveSessions();
    return () => {
      cancelled = true;
    };
  }, [themes]);

  async function handleStart(themeId: string) {
    setError(null);
    setStartingId(themeId);
    try {
      const session = await createSession({ customThemeId: themeId });
      router.push(`/student/tests/sessions/${session.id}`);
    } catch (err) {
      setStartingId(null);
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось начать тему. Попробуйте позже.",
      );
    }
  }

  function handleContinue(sessionId: string) {
    router.push(`/student/tests/sessions/${sessionId}`);
  }

  if (themes.length === 0) {
    return (
      <p className="text-sm text-zinc-500">
        Преподаватель ещё не опубликовал темы.
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

      <ul className="chem-card divide-y divide-zinc-200 overflow-hidden rounded-xl">
        {themes.map((theme) => {
          const activeSessionId = activeSessions[theme.id];
          const isStarting = startingId === theme.id;

          return (
            <li
              key={theme.id}
              className="flex items-center justify-between gap-3 px-4 py-3.5 sm:px-5"
            >
              <div className="min-w-0">
                <p className="font-medium text-zinc-900">{theme.title}</p>
                {theme.description ? (
                  <p className="mt-0.5 truncate text-sm text-zinc-500">
                    {theme.description}
                  </p>
                ) : null}
                <p className="mt-1 text-xs text-zinc-400">
                  {theme.task_count}{" "}
                  {theme.task_count === 1
                    ? "задание"
                    : theme.task_count < 5
                      ? "задания"
                      : "заданий"}
                </p>
              </div>
              {activeSessionId ? (
                <button
                  type="button"
                  onClick={() => handleContinue(activeSessionId)}
                  disabled={loadingActive}
                  className="chem-btn-primary min-h-[44px] shrink-0 px-5 py-2 text-sm disabled:opacity-60"
                >
                  Продолжить
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => void handleStart(theme.id)}
                  disabled={startingId !== null || loadingActive}
                  className="chem-btn-primary min-h-[44px] shrink-0 px-5 py-2 text-sm disabled:opacity-60"
                >
                  {isStarting ? "Запуск…" : "Начать"}
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
