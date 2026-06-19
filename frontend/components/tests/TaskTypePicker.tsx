"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { createSession, getActiveSession } from "@/lib/api/tests";
import type { TestTaskType } from "@/lib/api/types";

export function TaskTypePicker({ taskTypes }: { taskTypes: TestTaskType[] }) {
  const router = useRouter();
  const [startingType, setStartingType] = useState<number | null>(null);
  const [activeSessions, setActiveSessions] = useState<Record<number, string>>(
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
          taskTypes.map(async (item) => {
            const result = await getActiveSession({ taskType: item.type });
            return [item.type, result.session_id] as const;
          }),
        );
        if (!cancelled) {
          const map: Record<number, string> = {};
          for (const [type, sessionId] of entries) {
            if (sessionId) {
              map[type] = sessionId;
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
  }, [taskTypes]);

  async function handleStart(taskType: number) {
    setError(null);
    setStartingType(taskType);
    try {
      const session = await createSession({ types: [taskType] });
      router.push(`/student/tests/sessions/${session.id}`);
    } catch (err) {
      setStartingType(null);
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось начать тест. Попробуйте позже.",
      );
    }
  }

  function handleContinue(sessionId: string) {
    router.push(`/student/tests/sessions/${sessionId}`);
  }

  if (taskTypes.length === 0) {
    return (
      <p className="text-sm text-zinc-500">
        Задания недоступны. Проверьте подключение к API.
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
        {taskTypes.map((item) => {
          const activeSessionId = activeSessions[item.type];
          const isStarting = startingType === item.type;

          return (
            <li
              key={item.type}
              className="flex items-center justify-between gap-3 px-4 py-3.5 sm:px-5"
            >
              <div>
                <span className="font-medium text-zinc-900">
                  Задание {item.type}
                </span>
                <p className="mt-0.5 text-xs text-zinc-500">
                  {item.variant_count}{" "}
                  {item.variant_count === 1 ? "вариант" : "вариантов"}
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
                  onClick={() => handleStart(item.type)}
                  disabled={startingType !== null || loadingActive}
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
