"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { createHomeworkTestSession } from "@/lib/api/tests";
import { ApiError } from "@/lib/api/client";

export function TestHomeworkActions({
  homeworkId,
}: {
  homeworkId: string;
}) {
  const router = useRouter();
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleStart() {
    setError(null);
    setStarting(true);
    try {
      const session = await createHomeworkTestSession(homeworkId);
      router.push(`/student/tests/sessions/${session.id}`);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось начать тестовую сессию.",
      );
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div aria-live="polite">
        {error ? (
          <p role="alert" className="text-sm text-[var(--chem-crimson)]">
            {error}
          </p>
        ) : null}
      </div>
      <button
        type="button"
        onClick={handleStart}
        disabled={starting}
        className="chem-btn-primary inline-flex min-h-[44px] w-fit items-center px-4 py-2 text-sm disabled:opacity-60"
      >
        {starting ? "Запуск…" : "Начать тест"}
      </button>
      <p className="text-xs text-zinc-500">
        После завершения теста вернитесь сюда или сдайте задание на экране итогов.
      </p>
    </div>
  );
}
