"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { completeHomeworkItem } from "@/lib/api/homework";
import { ApiError } from "@/lib/api/client";

export function LectureHomeworkSubmit({
  homeworkId,
  itemIndex,
  topic,
}: {
  homeworkId: string;
  itemIndex: number;
  topic: string;
}) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function handleSubmit() {
    setError(null);
    setSubmitting(true);
    try {
      await completeHomeworkItem(homeworkId, itemIndex);
      setDone(true);
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setDone(true);
      } else {
        setError(
          err instanceof ApiError
            ? err.message
            : "Не удалось отметить задание как прочитанное.",
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <p className="text-sm text-chem-green">
        Пункт по теме «{topic}» отмечен как прочитанный.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {error ? (
        <p role="alert" className="text-sm text-[var(--chem-crimson)]">
          {error}
        </p>
      ) : null}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={submitting}
        className="inline-flex w-fit rounded-md border border-chem-royal px-4 py-2 text-sm font-medium text-chem-royal transition hover:bg-chem-royal/5 disabled:opacity-60"
      >
        {submitting ? "Отправка…" : "Прочитано"}
      </button>
    </div>
  );
}
