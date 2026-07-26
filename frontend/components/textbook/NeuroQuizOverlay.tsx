"use client";

import {
  useCallback,
  useEffect,
  useState,
  type CSSProperties,
} from "react";

import {
  answerNeuroQuiz,
  getNeuroQuizSession,
  skipNeuroQuiz,
  voteNeuroQuiz,
} from "@/lib/api/neuroquiz";
import { ApiError, formatFetchError } from "@/lib/api/client";
import type {
  NeuroQuizQuestionPublic,
  NeuroQuizSession,
  NeuroQuizSubmitResult,
} from "@/lib/api/types";

type OverlayPhase = "loading" | "question" | "failed";

const SALUTE_MS = 1600;

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function ThumbUpIcon({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      className={className}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M7 10v10M14.5 4.5 13 9h5.2a2 2 0 0 1 1.95 2.45l-1.35 6A2 2 0 0 1 16.85 19H7V9.5L12 4.5a1.5 1.5 0 0 1 2.5 1Z"
      />
    </svg>
  );
}

function ThumbDownIcon({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      className={className}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M17 14V4M9.5 19.5 11 15H5.8a2 2 0 0 1-1.95-2.45l1.35-6A2 2 0 0 1 7.15 5H17v9.5L12 19.5a1.5 1.5 0 0 1-2.5-1Z"
      />
    </svg>
  );
}

/** Subtle CSS burst on correct answer; skipped when prefers-reduced-motion. */
function CorrectSalute({ active }: { active: boolean }) {
  if (!active) {
    return null;
  }
  const particles = Array.from({ length: 14 }, (_, i) => i);
  return (
    <div
      className="neuroquiz-salute pointer-events-none absolute inset-0 overflow-hidden"
      data-testid="neuroquiz-salute"
      aria-hidden="true"
    >
      {particles.map((i) => (
        <span
          key={i}
          className="neuroquiz-salute__particle"
          style={
            {
              "--nq-angle": `${(360 / particles.length) * i}deg`,
              "--nq-delay": `${(i % 5) * 40}ms`,
              "--nq-hue": `${(i * 27) % 360}`,
            } as CSSProperties
          }
        />
      ))}
    </div>
  );
}

export function NeuroQuizOverlay({
  topic,
  chunkIdx,
  open,
  onSkip,
  onComplete,
}: {
  topic: string;
  chunkIdx: number;
  open: boolean;
  onSkip: () => void;
  onComplete: () => void;
}) {
  const [phase, setPhase] = useState<OverlayPhase>("loading");
  const [session, setSession] = useState<NeuroQuizSession | null>(null);
  const [index, setIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<NeuroQuizSubmitResult | null>(null);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [voted, setVoted] = useState<"like" | "dislike" | null>(null);
  const [showSalute, setShowSalute] = useState(false);

  const loadSession = useCallback(async () => {
    setPhase("loading");
    setError(null);
    setResult(null);
    setVoted(null);
    setSelectedOptionId(null);
    setShowSalute(false);
    setIndex(0);
    try {
      const data = await getNeuroQuizSession(topic, chunkIdx);
      setSession(data);
      setPhase("question");
    } catch (err) {
      setSession(null);
      setPhase("failed");
      setError(
        formatFetchError(
          err,
          err instanceof ApiError ? err.message : "Не удалось загрузить квиз.",
        ),
      );
    }
  }, [topic, chunkIdx]);

  useEffect(() => {
    if (!open) {
      return;
    }
    void loadSession();
  }, [open, loadSession]);

  useEffect(() => {
    if (!open) {
      return;
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        void handleSkip();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
    // handleSkip is stable enough via topic/chunkIdx; avoid rebind loops
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, topic, chunkIdx]);

  useEffect(() => {
    if (!showSalute) {
      return;
    }
    const timer = window.setTimeout(() => setShowSalute(false), SALUTE_MS);
    return () => window.clearTimeout(timer);
  }, [showSalute]);

  async function handleSkip() {
    try {
      await skipNeuroQuiz(topic, chunkIdx);
    } catch {
      // skip is best-effort telemetry
    }
    onSkip();
  }

  const question: NeuroQuizQuestionPublic | null =
    session?.questions[index] ?? null;
  const total = session?.questions.length ?? 0;

  async function handleAnswer(optionId: string) {
    if (!question || result || submitting) {
      return;
    }
    setSubmitting(true);
    setError(null);
    setSelectedOptionId(optionId);
    try {
      const submit = await answerNeuroQuiz(
        topic,
        chunkIdx,
        question.id,
        optionId,
      );
      setResult(submit);
      if (submit.correct && !prefersReducedMotion()) {
        setShowSalute(true);
      }
    } catch (err) {
      setSelectedOptionId(null);
      setError(
        formatFetchError(
          err,
          err instanceof ApiError ? err.message : "Не удалось отправить ответ.",
        ),
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVote(value: "like" | "dislike") {
    if (!question || !result || voted) {
      return;
    }
    try {
      await voteNeuroQuiz(question.id, value);
      setVoted(value);
    } catch (err) {
      setError(
        formatFetchError(
          err,
          err instanceof ApiError ? err.message : "Не удалось сохранить оценку.",
        ),
      );
    }
  }

  async function handleNext() {
    if (!result) {
      return;
    }
    // Server locked the pass — advance the textbook.
    if (result.quiz_completed) {
      onComplete();
      return;
    }
    // More questions still in this cached batch.
    if (index < total - 1) {
      setIndex((value) => value + 1);
      setResult(null);
      setVoted(null);
      setSelectedOptionId(null);
      setShowSalute(false);
      setError(null);
      return;
    }
    // Mid-pass resume: last cached question answered but pass not locked —
    // reload unanswered list from the server.
    setPhase("loading");
    setError(null);
    setResult(null);
    setVoted(null);
    setSelectedOptionId(null);
    setShowSalute(false);
    setIndex(0);
    try {
      const data = await getNeuroQuizSession(topic, chunkIdx);
      if (data.questions.length === 0) {
        onComplete();
        return;
      }
      setSession(data);
      setPhase("question");
    } catch (err) {
      setSession(null);
      setPhase("failed");
      setError(
        formatFetchError(
          err,
          err instanceof ApiError ? err.message : "Не удалось загрузить квиз.",
        ),
      );
    }
  }

  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-40 flex items-end justify-center bg-zinc-900/45 p-4 sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="neuroquiz-title"
    >
      <div className="chem-card relative w-full max-w-lg overflow-hidden rounded-xl border border-chem-teal/20 bg-white p-5 shadow-lg">
        <CorrectSalute active={showSalute} />
        <div className="relative flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-chem-teal">
              Нейроквиз
            </p>
            <h2
              id="neuroquiz-title"
              className="mt-1 text-lg font-semibold text-zinc-900"
            >
              {phase === "question" && question
                ? `Вопрос ${index + 1} из ${total}`
                : "Проверка по чанку"}
            </h2>
          </div>
        </div>

        {phase === "loading" ? (
          <div className="relative mt-6 space-y-4" aria-live="polite">
            <p className="text-sm text-zinc-600">Готовим вопросы…</p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void loadSession()}
                className="min-h-[44px] rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50"
              >
                Повторить
              </button>
              <button
                type="button"
                onClick={() => void handleSkip()}
                className="min-h-[44px] rounded-md px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-50"
              >
                Пропустить квиз
              </button>
            </div>
          </div>
        ) : null}

        {phase === "failed" ? (
          <div className="relative mt-6 space-y-4" role="alert">
            <p className="text-sm text-red-600">
              {error ?? "Не удалось загрузить квиз."}
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void loadSession()}
                className="min-h-[44px] rounded-md border border-chem-teal bg-chem-teal-soft px-4 py-2 text-sm font-medium text-chem-teal-dark"
              >
                Повторить
              </button>
              <button
                type="button"
                onClick={() => void handleSkip()}
                className="min-h-[44px] rounded-md px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-50"
              >
                Пропустить квиз
              </button>
            </div>
          </div>
        ) : null}

        {phase === "question" && question ? (
          <div className="relative mt-5 space-y-4">
            <div>
              <p className="text-base text-zinc-800">{question.prompt}</p>
              {result ? (
                <div
                  className="mt-2 flex justify-end gap-1"
                  role="group"
                  aria-label="Оценка вопроса"
                >
                  <button
                    type="button"
                    disabled={voted !== null}
                    onClick={() => void handleVote("like")}
                    aria-label="Полезно"
                    aria-pressed={voted === "like"}
                    className={
                      voted === "like"
                        ? "inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-md border border-chem-teal bg-chem-teal-soft text-chem-teal-dark"
                        : "inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-md border border-zinc-300 text-zinc-600 hover:bg-zinc-50 disabled:opacity-50"
                    }
                  >
                    <ThumbUpIcon className="h-5 w-5" />
                  </button>
                  <button
                    type="button"
                    disabled={voted !== null}
                    onClick={() => void handleVote("dislike")}
                    aria-label="Плохой вопрос"
                    aria-pressed={voted === "dislike"}
                    className={
                      voted === "dislike"
                        ? "inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-md border border-red-300 bg-red-50 text-red-700"
                        : "inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-md border border-zinc-300 text-zinc-600 hover:bg-zinc-50 disabled:opacity-50"
                    }
                  >
                    <ThumbDownIcon className="h-5 w-5" />
                  </button>
                </div>
              ) : null}
            </div>

            <div className="flex flex-col gap-2" role="group" aria-label="Варианты ответа">
              {question.options.map((option) => {
                const answered = Boolean(result);
                const isCorrect =
                  result && option.id === result.correct_option_id;
                const isWrongPick =
                  result &&
                  !result.correct &&
                  option.id === selectedOptionId;
                let optionClass =
                  "min-h-[44px] rounded-md border border-zinc-300 px-4 py-3 text-left text-sm text-zinc-800 transition hover:bg-zinc-50 disabled:opacity-100";
                if (answered && isCorrect) {
                  optionClass =
                    "min-h-[44px] rounded-md border border-emerald-500 bg-emerald-50 px-4 py-3 text-left text-sm text-emerald-900";
                } else if (answered && isWrongPick) {
                  optionClass =
                    "min-h-[44px] rounded-md border border-red-400 bg-red-50 px-4 py-3 text-left text-sm text-red-900";
                } else if (answered) {
                  optionClass =
                    "min-h-[44px] rounded-md border border-zinc-200 bg-zinc-50 px-4 py-3 text-left text-sm text-zinc-500";
                }
                return (
                  <button
                    key={option.id}
                    type="button"
                    disabled={answered || submitting}
                    onClick={() => void handleAnswer(option.id)}
                    className={optionClass}
                  >
                    {option.text}
                  </button>
                );
              })}
            </div>

            {result ? (
              <div className="space-y-3" aria-live="polite">
                <p
                  className={
                    result.correct
                      ? "text-sm font-medium text-emerald-700"
                      : "text-sm font-medium text-red-700"
                  }
                >
                  {result.correct
                    ? result.points_awarded > 0
                      ? "Верно! +1 балл"
                      : "Верно"
                    : "Неверно"}
                </p>
                {result.explanation ? (
                  <p className="text-sm text-zinc-600">{result.explanation}</p>
                ) : null}
              </div>
            ) : null}

            {error ? (
              <p className="text-sm text-red-600" role="alert">
                {error}
              </p>
            ) : null}

            <div className="flex flex-col gap-2 border-t border-zinc-100 pt-4">
              <button
                type="button"
                disabled={!result}
                onClick={() => void handleNext()}
                className="min-h-[44px] w-full rounded-md bg-chem-teal px-4 py-2 text-sm font-medium text-white hover:bg-chem-teal/90 disabled:opacity-40"
              >
                Далее
              </button>
              <button
                type="button"
                onClick={() => void handleSkip()}
                className="min-h-[44px] w-full rounded-md px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-50"
              >
                Пропустить квиз
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
