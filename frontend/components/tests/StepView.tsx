"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { checkStep, completeSession } from "@/lib/api/tests";
import type { TestSession, TestStep } from "@/lib/api/types";
import { QuestionContent } from "@/components/tests/QuestionContent";
import { StepProgressDots } from "@/components/tests/StepProgressDots";
import { useTutorChat } from "@/lib/tutor/TutorChatContext";

function findFirstUnchecked(steps: TestStep[]): number {
  const index = steps.findIndex((step) => step.status !== "checked");
  return index === -1 ? 0 : index;
}

export function StepView({ session }: { session: TestSession }) {
  const router = useRouter();
  const { openTutor } = useTutorChat();
  const initialIndex = findFirstUnchecked(session.steps);
  const [steps, setSteps] = useState<TestStep[]>(session.steps);
  const [current, setCurrent] = useState(initialIndex);
  const [answer, setAnswer] = useState(
    session.steps[initialIndex]?.answer ?? "",
  );
  const [checking, setChecking] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const step = steps[current];
  const isLast = current === steps.length - 1;

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
            ? {
                ...s,
                answer,
                is_correct: result.is_correct,
                status: "checked",
              }
            : s,
        ),
      );
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
  const showAskTutor =
    isChecked && step.is_correct === false && step.test_id != null;

  function handleAskTutor() {
    const studentAnswer = (step.answer ?? answer).trim();
    openTutor({
      pageContext: {
        test_session_id: session.id,
        step_position: step.position,
        test_id: step.test_id,
        solve_mode: "explain_incorrect_step",
      },
      initialMessage: `Разбери задание ${step.test_id}. Мой ответ: «${studentAnswer || "—"}». Объясни, в чём ошибка, и сравни с правильным ответом.`,
      autoSendInitialMessage: true,
    });
  }

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

          {showAskTutor ? (
            <div className="mt-4">
              <button
                type="button"
                onClick={handleAskTutor}
                className="chem-btn-ghost min-h-[44px] px-3 py-2 text-sm text-chem-teal"
              >
                Спросить советчика
              </button>
            </div>
          ) : null}

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
