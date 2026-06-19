"use client";

import type { OnboardingChecklist } from "@/lib/api/types";

const STEPS: Array<{
  key: keyof OnboardingChecklist;
  label: string;
}> = [
  { key: "login", label: "Войти в кабинет" },
  { key: "first_action", label: "Сделать первое задание или тест" },
  { key: "lecture", label: "Открыть лекцию в учебнике" },
];

export function OnboardingChecklist({
  checklist,
}: {
  checklist: OnboardingChecklist;
}) {
  const completed = STEPS.filter((step) => checklist[step.key]).length;
  const allDone = completed === STEPS.length;

  if (allDone) {
    return null;
  }

  return (
    <section
      aria-labelledby="onboarding-checklist-title"
      className="chem-card rounded-xl p-4 sm:p-5"
    >
      <div className="flex items-center justify-between gap-3">
        <h2
          id="onboarding-checklist-title"
          className="text-base font-semibold text-zinc-900"
        >
          Первые шаги
        </h2>
        <span className="text-sm font-medium text-chem-teal-dark">
          {completed}/{STEPS.length}
        </span>
      </div>
      <ul className="mt-4 space-y-2">
        {STEPS.map((step) => {
          const done = checklist[step.key];
          return (
            <li key={step.key} className="flex items-start gap-3 text-sm">
              <span
                aria-hidden
                className={
                  done
                    ? "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-chem-teal text-xs text-white"
                    : "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-zinc-300 text-zinc-400"
                }
              >
                {done ? "✓" : ""}
              </span>
              <span className={done ? "text-zinc-500 line-through" : "text-zinc-700"}>
                {step.label}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
