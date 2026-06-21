"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { reopenHomework } from "@/lib/api/homework";
import { ApiError } from "@/lib/api/client";

export function HomeworkReopenButton({ homeworkId }: { homeworkId: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleReopen() {
    setError(null);
    setLoading(true);
    try {
      await reopenHomework(homeworkId);
      router.refresh();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось открыть задание для досдачи.",
      );
    } finally {
      setLoading(false);
    }
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
        onClick={handleReopen}
        disabled={loading}
        className="chem-btn-primary inline-flex min-h-[44px] w-fit items-center px-4 py-2 text-sm disabled:opacity-60"
      >
        {loading ? "Открытие…" : "Досдать"}
      </button>
    </div>
  );
}
