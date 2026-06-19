"use client";

import { useState } from "react";

import { TaskTypePicker } from "@/components/tests/TaskTypePicker";
import { VariantPicker } from "@/components/tests/VariantPicker";
import type { TestTaskType, TestVariant, Track } from "@/lib/api/types";

type TestsViewMode = "variants" | "task-types";

export function TestsPicker({
  variants,
  taskTypes,
  track,
}: {
  variants: TestVariant[];
  taskTypes: TestTaskType[];
  track: Track;
}) {
  const showTaskTypes = track === "ege";
  const [mode, setMode] = useState<TestsViewMode>("variants");

  return (
    <div className="flex flex-col gap-6">
      {showTaskTypes ? (
        <div
          role="tablist"
          aria-label="Режим выбора тестов"
          className="inline-flex w-full rounded-lg border border-zinc-200 bg-zinc-50 p-1 sm:w-auto"
        >
          <button
            type="button"
            role="tab"
            aria-selected={mode === "variants"}
            onClick={() => setMode("variants")}
            className={`min-h-[44px] flex-1 rounded-md px-4 py-2 text-sm font-medium transition sm:flex-none ${
              mode === "variants"
                ? "bg-white text-zinc-900 shadow-sm"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            По вариантам
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "task-types"}
            onClick={() => setMode("task-types")}
            className={`min-h-[44px] flex-1 rounded-md px-4 py-2 text-sm font-medium transition sm:flex-none ${
              mode === "task-types"
                ? "bg-white text-zinc-900 shadow-sm"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            По заданиям
          </button>
        </div>
      ) : null}

      {mode === "variants" || !showTaskTypes ? (
        <VariantPicker variants={variants} />
      ) : (
        <TaskTypePicker taskTypes={taskTypes} />
      )}
    </div>
  );
}
