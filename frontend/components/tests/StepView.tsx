"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import {
  checkStep,
  completeSession,
  getHint,
} from "@/lib/api/tests";
import type { TestSession, TestStep } from "@/lib/api/types";
import { QuestionContent } from "@/components/tests/QuestionContent";
import { StepProgressDots } from "@/components/tests/StepProgressDots";

function findFirstUnchecked(steps: TestStep[]): number {
  const index = steps.findIndex((step) => step.status !== "checked");
  return index === -1 ? 0 : index;
}

function buildInitialExplanations(
  steps: TestStep[],
): Record<number, string | null> {
  const map: Record<number, string | null> = {};
  steps.forEach((step, index) => {
    if (step.status === "checked" && step.detailed_explanation) {
      map[index] = step.detailed_explanation;
    }
  });
  return map;
}

function buildInitialExplanationVisibility(
  steps: TestStep[],
): Record<number, boolean> {
  const map: Record<number, boolean> = {};
  steps.forEach((step, index) => {
    if (step.status === "checked" && step.detailed_explanation) {
      map[index] = true;
    }
  });
  return map;
}

export function StepView({ session }: { session: TestSession }) {
  const router = useRouter();
  const initialIndex = findFirstUnchecked(session.steps);
  const [steps, setSteps] = useState<TestStep[]>(session.steps);
  const [current, setCurrent] = useState(initialIndex);
  const [answer, setAnswer] = useState(
    session.steps[initialIndex]?.answer ?? "",
  );
  const [hints, setHints] = useState<Record<number, string | null>>({});
  const [explanations, setExplanations] = useState<Record<number, string | null>>(
    () => buildInitialExplanations(session.steps),
  );
  const [showExplanation, setShowExplanation] = useState<Record<number, boolean>>(
    () => buildInitialExplanationVisibility(session.steps),
  );
  const [checking, setChecking] = useState(false);
  const [hintLoading, setHintLoading] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const step = steps[current];
  const isLast = current === steps.length - 1;
  const hintShown = current in hints;
  const explanation = explanations[current];
  const explanationVisible = showExplanation[current] ?? false;

  const checkedCount = useMemo(
    () => steps.filter((s) => s.status === "checked").length,
    [steps],
  );

  useEffect(() => {
    let cancelled = false;

    async function restoreHints() {
      for (let index = 0; index < session.steps.length; index += 1) {
        const sessionStep = session.steps[index];
        if (!sessionStep.hint_used) {
          continue;
        }
        try {
          const result = await getHint(session.id, sessionStep.position);
          if (!cancelled) {
            setHints((prev) => ({ ...prev, [index]: result.hint }));
          }
        } catch {
          // Resume should not block the session if hint restore fails.
        }
      }
    }

    void restoreHints();
    return () => {
      cancelled = true;
    };
  }, [session.id, session.steps]);

  function goTo(index: number) {
    setCurrent(index);
    setAnswer(steps[index]?.answer ?? "");
    setError(null);
  }

  async function handleCheck() {
    if (!step) {
      return;
    }
    setError(null);
    setChecking(true);
    try {
      const result = await checkStep(session.id, step.position, answer);
      setSteps((prev) =>
        prev.map((s) =>
          s.position === step.position
            ? {
                ...s,
                answer,
                is_correct: result.is_correct,
                status: "checked",
                detailed_explanation: result.detailed_explanation,
              }
            : s,
        ),
      );
      setExplanations((prev) => ({
        ...prev,
        [current]: result.detailed_explanation,
      }));
      setShowExplanation((prev) => ({ ...prev, [current]: true }));
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось проверить ответ.",
      );
    } finally {
      setChecking(false);
    }
  }

  async function handleHint() {
    if (!step) {
      return;
    }
    setError(null);
    setHintLoading(true);
    try {
      const result = await getHint(session.id, step.position);
      setHints((prev) => ({ ...prev, [current]: result.hint }));
      setSteps((prev) =>
        prev.map((s) =>
          s.position === step.position
            ? { ...s, hint_used: true, status: s.status === "unseen" ? "answered" : s.status }
            : s,
        ),
      );
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Не удалось загрузить подсказку.",
      );
    } finally {
      setHintLoading(false);
    }
  }

  function handleToggleExplanation() {
    setShowExplanation((prev) => ({
      ...prev,
      [current]: !explanationVisible,
    }));
  }

  async function handleComplete() {
    setError(null);
    setCompleting(true);
    try {
      await completeSession(session.id);
      router.push(`/student/tests/sessions/${session.id}/summary`);
    } catch (err) {
      setCompleting(false);
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось завершить тест.",
      );
    }
  }

  if (!step) {
    return <p className="text-sm text-zinc-500">В этом тесте нет заданий.</p>;
  }

  const isChecked = step.status === "checked";

  return (
    <div className="flex min-w-0 flex-col gap-4">
      <StepProgressDots
        steps={steps}
        current={current}
        onSelect={goTo}
      />

      <article className="chem-card overflow-hidden rounded-xl pb-36 sm:pb-6">
        <header className="flex items-center gap-4 bg-chem-teal px-4 py-4 text-white sm:px-5">
          <span
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/20 text-sm font-bold"
            aria-label={`Задание ${current + 1}`}
          >
            {current + 1}
          </span>
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wide text-white/75">
              Задание
            </p>
            <h2 className="truncate text-lg font-semibold">Тип {step.type}</h2>
          </div>
        </header>

        <div className="min-w-0 px-4 py-6 sm:px-5">
          <QuestionContent text={step.question} />

          <div className="mt-5 flex flex-col gap-2">
            <label
              htmlFor="answer-input"
              className="text-sm font-medium text-zinc-700"
            >
              Ваш ответ
            </label>
            <input
              id="answer-input"
              type="text"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              className="chem-input min-h-[44px] w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900"
            />
          </div>

          {isChecked ? (
            <p
              role="status"
              aria-live="polite"
              className={`mt-4 px-3 py-2 text-sm ${
                step.is_correct ? "chem-verdict-correct" : "chem-verdict-incorrect"
              }`}
            >
              {step.is_correct ? "✓ Верно" : "✗ Неверно"}
            </p>
          ) : null}

          {hintShown ? (
            <div className="chem-callout chem-callout-important mt-4">
              <span className="font-semibold text-chem-teal-dark">Подсказка: </span>
              {hints[current] ?? "Подсказка отсутствует."}
            </div>
          ) : null}

          {isChecked && explanation && explanationVisible ? (
            <div
              id="step-explanation"
              className="chem-callout chem-callout-example mt-4"
            >
              <span className="font-semibold text-chem-teal-dark">Разбор: </span>
              <span className="whitespace-pre-wrap">{explanation}</span>
            </div>
          ) : null}

          {error ? (
            <p role="alert" className="mt-4 text-sm text-[var(--chem-crimson)]">
              {error}
            </p>
          ) : null}
        </div>
      </article>

      <div
        className="fixed bottom-0 left-0 right-0 z-10 border-t border-zinc-200 bg-white/95 backdrop-blur-sm sm:static sm:border-t-0 sm:bg-transparent sm:backdrop-blur-none"
        aria-label="Действия с заданием"
      >
        <div className="mx-auto flex max-w-3xl flex-col gap-2 px-4 py-3 sm:px-0">
          <div className="flex gap-2 sm:mt-2">
            <button
              type="button"
              onClick={handleCheck}
              disabled={checking || answer.trim() === "" || isChecked}
              className="chem-btn-primary min-h-[44px] flex-1 px-4 py-2.5 text-sm disabled:opacity-60 sm:flex-none sm:px-5"
            >
              {checking ? "Проверка…" : "Проверить"}
            </button>
            <button
              type="button"
              onClick={handleHint}
              disabled={hintLoading || hintShown}
              className="chem-btn-secondary min-h-[44px] flex-1 px-4 py-2.5 text-sm disabled:opacity-55 sm:flex-none sm:px-5"
            >
              {hintLoading ? "Загрузка…" : "Подсказка"}
            </button>
            <button
              type="button"
              onClick={handleToggleExplanation}
              disabled={!isChecked || !explanation}
              className="chem-btn-secondary min-h-[44px] flex-1 px-4 py-2.5 text-sm disabled:opacity-55 sm:flex-none sm:px-5"
              aria-expanded={explanationVisible}
              aria-controls="step-explanation"
            >
              {explanationVisible ? "Скрыть разбор" : "Разбор"}
            </button>
          </div>
        </div>

        <nav
          aria-label="Навигация по заданиям"
          className="border-t border-zinc-200 px-4 py-3 sm:mt-2 sm:border-t sm:border-zinc-200 sm:px-0"
        >
          <div className="mx-auto flex max-w-3xl items-center justify-between gap-3">
            <button
              type="button"
              onClick={() => goTo(current - 1)}
              disabled={current === 0}
              className="chem-btn-ghost min-h-[44px] min-w-[44px] px-4 py-2 text-sm disabled:opacity-40"
            >
              ← Назад
            </button>

            <span className="text-center text-sm text-zinc-500">
              Проверено {checkedCount} из {steps.length}
            </span>

            {isLast ? (
              <button
                type="button"
                onClick={handleComplete}
                disabled={completing}
                className="chem-btn-primary min-h-[44px] min-w-[44px] px-4 py-2 text-sm disabled:opacity-60"
              >
                {completing ? "…" : "Завершить"}
              </button>
            ) : (
              <button
                type="button"
                onClick={() => goTo(current + 1)}
                className="chem-btn-ghost min-h-[44px] min-w-[44px] px-4 py-2 text-sm"
              >
                Далее →
              </button>
            )}
          </div>
        </nav>
      </div>
    </div>
  );
}
