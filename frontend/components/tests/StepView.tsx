"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import {
  checkStep,
  completeSession,
  getHint,
} from "@/lib/api/tests";
import type { TestSession, TestStep } from "@/lib/api/types";
import { ProgressBar } from "@/components/tests/ProgressBar";
import { QuestionContent } from "@/components/tests/QuestionContent";

export function StepView({ session }: { session: TestSession }) {
  const router = useRouter();
  const [steps, setSteps] = useState<TestStep[]>(session.steps);
  const [current, setCurrent] = useState(0);
  const [answer, setAnswer] = useState(session.steps[0]?.answer ?? "");
  const [hints, setHints] = useState<Record<number, string | null>>({});
  const [explanations, setExplanations] = useState<Record<number, string | null>>(
    {},
  );
  const [checking, setChecking] = useState(false);
  const [hintLoading, setHintLoading] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const step = steps[current];
  const isLast = current === steps.length - 1;
  const hintShown = current in hints;
  const explanation = explanations[current];

  const checkedCount = useMemo(
    () => steps.filter((s) => s.status === "checked").length,
    [steps],
  );

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
            ? { ...s, answer, is_correct: result.is_correct, status: "checked" }
            : s,
        ),
      );
      setExplanations((prev) => ({
        ...prev,
        [current]: result.detailed_explanation,
      }));
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
          s.position === step.position ? { ...s, hint_used: true } : s,
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
    <div className="flex flex-col gap-6">
      <ProgressBar current={current + 1} total={steps.length} />

      <article className="chem-card rounded-lg p-6">
        <p className="chem-kicker text-sm normal-case tracking-normal">
          Задание {step.type}
        </p>

        <div className="mt-3">
          <QuestionContent text={step.question} />
        </div>

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
            className="chem-input rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900"
          />
        </div>

        {isChecked ? (
          <p
            role="status"
            className={`mt-4 text-sm font-semibold ${
              step.is_correct
                ? "text-[var(--chem-green)]"
                : "text-[var(--chem-crimson)]"
            }`}
          >
            {step.is_correct ? "✓ Верно" : "✗ Неверно"}
          </p>
        ) : null}

        {hintShown ? (
          <div className="mt-4 rounded-md border border-chem-peach/50 bg-chem-peach/10 p-3 text-sm text-zinc-800">
            <span className="font-medium">Подсказка: </span>
            {hints[current] ?? "Подсказка отсутствует."}
          </div>
        ) : null}

        {isChecked && explanation ? (
          <div className="mt-4 rounded-md border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-800">
            <span className="font-medium">Разбор: </span>
            <span className="whitespace-pre-wrap">{explanation}</span>
          </div>
        ) : null}

        {error ? (
          <p role="alert" className="mt-4 text-sm text-[var(--chem-crimson)]">
            {error}
          </p>
        ) : null}

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleCheck}
            disabled={checking || answer.trim() === ""}
            className="chem-btn-primary px-4 py-2 text-sm disabled:opacity-60"
          >
            {checking ? "Проверка…" : "Проверить"}
          </button>
          <button
            type="button"
            onClick={handleHint}
            disabled={hintLoading || hintShown}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 disabled:opacity-50"
          >
            {hintLoading ? "Загрузка…" : "Подсказка"}
          </button>
        </div>
      </article>

      <div className="flex items-center justify-between gap-4">
        <button
          type="button"
          onClick={() => goTo(current - 1)}
          disabled={current === 0}
          className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 disabled:opacity-40"
        >
          ← Назад
        </button>

        <span className="text-sm text-zinc-500">
          Проверено {checkedCount} из {steps.length}
        </span>

        {isLast ? (
          <button
            type="button"
            onClick={handleComplete}
            disabled={completing}
            className="chem-btn-primary px-4 py-2 text-sm disabled:opacity-60"
          >
            {completing ? "Завершение…" : "Завершить тест"}
          </button>
        ) : (
          <button
            type="button"
            onClick={() => goTo(current + 1)}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50"
          >
            Далее →
          </button>
        )}
      </div>
    </div>
  );
}
