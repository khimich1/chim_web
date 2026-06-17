"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { createSession } from "@/lib/api/tests";
import type { TestVariant } from "@/lib/api/types";

export function VariantPicker({ variants }: { variants: TestVariant[] }) {
  const router = useRouter();
  const [startingRef, setStartingRef] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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
        {variants.map((variant) => (
          <li
            key={variant.filename}
            className="flex items-center justify-between gap-3 px-4 py-3.5 sm:px-5"
          >
            <span className="font-medium text-zinc-900">
              Вариант {variant.filename.replace(/\.txt$/, "")}
            </span>
            <button
              type="button"
              onClick={() => handleStart(variant.filename)}
              disabled={startingRef !== null}
              className="chem-btn-primary min-h-[44px] px-5 py-2 text-sm disabled:opacity-60"
            >
              {startingRef === variant.filename ? "Запуск…" : "Начать"}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
