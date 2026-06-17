"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { createSession, getActiveSession } from "@/lib/api/tests";
import type { TestVariant } from "@/lib/api/types";

export function VariantPicker({ variants }: { variants: TestVariant[] }) {
  const router = useRouter();
  const [startingRef, setStartingRef] = useState<string | null>(null);
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
          variants.map(async (variant) => {
            const result = await getActiveSession({
              variantRef: variant.filename,
            });
            return [variant.filename, result.session_id] as const;
          }),
        );
        if (!cancelled) {
          const map: Record<string, string> = {};
          for (const [filename, sessionId] of entries) {
            if (sessionId) {
              map[filename] = sessionId;
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
  }, [variants]);

  async function handleStart(variantRef: string) {
    setError(null);
    setStartingRef(variantRef);
    try {
      const session = await createSession(variantRef);
      router.push(`/student/tests/sessions/${session.id}`);
    } catch (err) {
      setStartingRef(null);
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

  if (variants.length === 0) {
    return (
      <p className="text-sm text-zinc-500">
        Варианты недоступны. Проверьте подключение к API.
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
        {variants.map((variant) => {
          const activeSessionId = activeSessions[variant.filename];
          const isStarting = startingRef === variant.filename;

          return (
            <li
              key={variant.filename}
              className="flex items-center justify-between gap-3 px-4 py-3.5 sm:px-5"
            >
              <span className="font-medium text-zinc-900">
                Вариант {variant.filename.replace(/\.txt$/, "")}
              </span>
              {activeSessionId ? (
                <button
                  type="button"
                  onClick={() => handleContinue(activeSessionId)}
                  disabled={loadingActive}
                  className="chem-btn-primary min-h-[44px] px-5 py-2 text-sm disabled:opacity-60"
                >
                  Продолжить
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => handleStart(variant.filename)}
                  disabled={startingRef !== null || loadingActive}
                  className="chem-btn-primary min-h-[44px] px-5 py-2 text-sm disabled:opacity-60"
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
