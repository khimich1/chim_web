"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { submitHomework } from "@/lib/api/homework";
import { ApiError } from "@/lib/api/client";

export function HomeworkSubmitButton({
  homeworkId,
  sessionId,
}: {
  homeworkId: string;
  sessionId?: string;
}) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    setError(null);
    setSubmitting(true);
    try {
      await submitHomework(homeworkId, sessionId);
      setDone(true);
      router.refresh();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось сдать домашнее задание.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <p
        className="text-sm font-medium text-[var(--text-positive)]"
        aria-live="polite"
      >
        Домашнее задание сдано. Преподаватель получит уведомление.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div aria-live="polite">
        {error ? (
          <p role="alert" className="text-sm text-[var(--chem-crimson)]">
            {error}
          </p>
        ) : null}
      </div>
      <button
        type="button"
        onClick={handleSubmit}
        disabled={submitting}
        className="chem-btn-primary inline-flex min-h-[44px] w-fit items-center px-4 py-2 text-sm disabled:opacity-60"
      >
        {submitting ? "Отправка…" : "Сдать домашнее задание"}
      </button>
    </div>
  );
}
