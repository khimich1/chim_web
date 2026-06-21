"use client";

import { useMemo, useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import QRCode from "react-qr-code";

import { CustomQuestionContent } from "@/components/tests/CustomQuestionContent";
import { QuestionContent } from "@/components/tests/QuestionContent";
import { StepProgressDots } from "@/components/tests/StepProgressDots";
import { ApiError } from "@/lib/api/client";
import { createHandoff } from "@/lib/api/handoff";
import { uploadImage } from "@/lib/api/uploads";
import {
  attachAnswerImage,
  checkStep,
  compareStep,
  completeSession,
  getSession,
} from "@/lib/api/tests";
import type { ContentBlock, TestSession, TestStep } from "@/lib/api/types";
import { useTutorChat } from "@/lib/tutor/TutorChatContext";
import {
  countsTowardScore,
  isCustomStep,
} from "@/lib/tests/grading-utils";

function findFirstUnchecked(steps: TestStep[]): number {
  const index = steps.findIndex((step) => step.status !== "checked");
  return index === -1 ? 0 : index;
}

function isCustomSession(session: TestSession): boolean {
  return (
    session.source === "custom" ||
    session.custom_theme_id != null ||
    session.steps.some(isCustomStep)
  );
}

function stepTitle(step: TestStep, index: number): string {
  if (isCustomStep(step)) {
    if (step.grading_mode === "self_check") {
      return "Самопроверка";
    }
    return "Авторское задание";
  }
  return `Тип ${step.type ?? index + 1}`;
}

export function StepView({ session }: { session: TestSession }) {
  const router = useRouter();
  const { openTutor } = useTutorChat();
  const customSession = isCustomSession(session);
  const initialIndex = findFirstUnchecked(session.steps);
  const [steps, setSteps] = useState<TestStep[]>(session.steps);
  const [current, setCurrent] = useState(initialIndex);
  const [answer, setAnswer] = useState(
    session.steps[initialIndex]?.answer ?? "",
  );
  const [referenceAnswer, setReferenceAnswer] = useState<ContentBlock[] | null>(
    null,
  );
  const [answerImageId, setAnswerImageId] = useState<string | null>(
    session.steps[initialIndex]?.answer_image_id ?? null,
  );
  const [answerImageUrl, setAnswerImageUrl] = useState<string | null>(
    session.steps[initialIndex]?.answer_image_url ?? null,
  );
  const [uploadingAnswerImage, setUploadingAnswerImage] = useState(false);
  const [handoffUrl, setHandoffUrl] = useState<string | null>(null);
  const [handoffLoading, setHandoffLoading] = useState(false);
  const [handoffPolling, setHandoffPolling] = useState(false);
  const [photoReceivedFromPhone, setPhotoReceivedFromPhone] = useState(false);
  const [checking, setChecking] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const step = steps[current];
  const isLast = current === steps.length - 1;
  const isSelfCheck = step?.grading_mode === "self_check";
  const isHomeworkSession = session.homework_assignment_id != null;
  const requiresPhoto = isHomeworkSession && isSelfCheck;
  const isChecked = step?.status === "checked";

  const checkedCount = useMemo(
    () => steps.filter((s) => s.status === "checked").length,
    [steps],
  );

  const scorableCount = useMemo(
    () => steps.filter(countsTowardScore).length,
    [steps],
  );

  function goTo(index: number) {
    setCurrent(index);
    setAnswer(steps[index]?.answer ?? "");
    setReferenceAnswer(null);
    setAnswerImageId(steps[index]?.answer_image_id ?? null);
    setAnswerImageUrl(steps[index]?.answer_image_url ?? null);
    setHandoffUrl(null);
    setHandoffPolling(false);
    setPhotoReceivedFromPhone(false);
    setError(null);
  }

  const pollHandoffPhoto = useCallback(async () => {
    if (!step) {
      return;
    }
    try {
      const updated = await getSession(session.id);
      const updatedStep = updated.steps.find((item) => item.position === step.position);
      if (!updatedStep?.answer_image_id) {
        return;
      }
      setAnswerImageId(updatedStep.answer_image_id);
      setAnswerImageUrl(updatedStep.answer_image_url ?? null);
      setSteps((prev) =>
        prev.map((item) =>
          item.position === step.position
            ? {
                ...item,
                answer_image_id: updatedStep.answer_image_id,
                answer_image_url: updatedStep.answer_image_url,
              }
            : item,
        ),
      );
      setPhotoReceivedFromPhone(true);
      setHandoffUrl(null);
      setHandoffPolling(false);
    } catch {
      // polling is best-effort until photo arrives or handoff expires
    }
  }, [session.id, step]);

  useEffect(() => {
    if (!requiresPhoto || !handoffPolling || answerImageId || isChecked) {
      return;
    }
    const intervalId = window.setInterval(() => {
      void pollHandoffPhoto();
    }, 2500);
    void pollHandoffPhoto();
    return () => window.clearInterval(intervalId);
  }, [
    requiresPhoto,
    handoffPolling,
    answerImageId,
    isChecked,
    pollHandoffPhoto,
  ]);

  async function handleStartHandoff() {
    if (!step) {
      return;
    }
    setError(null);
    setHandoffLoading(true);
    try {
      const result = await createHandoff(session.id, step.position);
      setHandoffUrl(result.capture_url);
      setHandoffPolling(true);
      setPhotoReceivedFromPhone(false);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось создать QR для съёмки.",
      );
    } finally {
      setHandoffLoading(false);
    }
  }

  function buildAnswerPayload(): string {
    return answer.trim();
  }

  async function handleAnswerImageUpload(file: File) {
    if (!step) {
      return;
    }
    setError(null);
    setUploadingAnswerImage(true);
    try {
      const result = await uploadImage(file);
      const attached = await attachAnswerImage(
        session.id,
        step.position,
        result.id,
      );
      setAnswerImageId(attached.answer_image_id);
      setAnswerImageUrl(attached.answer_image_url);
      setSteps((prev) =>
        prev.map((s) =>
          s.position === step.position
            ? {
                ...s,
                answer_image_id: attached.answer_image_id,
                answer_image_url: attached.answer_image_url,
              }
            : s,
        ),
      );
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось загрузить изображение.",
      );
    } finally {
      setUploadingAnswerImage(false);
    }
  }

  async function handleCheck() {
    if (!step) {
      return;
    }
    setError(null);
    setChecking(true);
    try {
      const payload = buildAnswerPayload();
      const result = await checkStep(session.id, step.position, payload);
      setSteps((prev) =>
        prev.map((s) =>
          s.position === step.position
            ? {
                ...s,
                answer: payload,
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

  async function handleCompare() {
    if (!step) {
      return;
    }
    setError(null);
    setChecking(true);
    try {
      const payload = buildAnswerPayload();
      const result = await compareStep(session.id, step.position, payload);
      setReferenceAnswer(result.reference_answer);
      setSteps((prev) =>
        prev.map((s) =>
          s.position === step.position
            ? {
                ...s,
                answer: payload,
                status: "checked",
                is_correct: null,
              }
            : s,
        ),
      );
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось сравнить ответ.",
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

  const showAskTutor =
    !customSession &&
    isChecked &&
    step.is_correct === false &&
    step.test_id != null;

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

  const actionDisabled = (() => {
    if (checking || isChecked) {
      return true;
    }
    if (isSelfCheck) {
      return requiresPhoto ? !answerImageId : false;
    }
    return answer.trim() === "";
  })();

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
            <h2 className="truncate text-lg font-semibold">
              {stepTitle(step, current)}
            </h2>
          </div>
        </header>

        <div className="min-w-0 px-4 py-6 sm:px-5">
          {isCustomStep(step) && step.question_blocks ? (
            <CustomQuestionContent blocks={step.question_blocks} />
          ) : step.question ? (
            <QuestionContent text={step.question} />
          ) : null}

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
              disabled={isChecked}
              className="chem-input min-h-[44px] w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 disabled:bg-zinc-50"
            />
            {requiresPhoto ? (
              <div className="flex flex-col gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={() => void handleStartHandoff()}
                    disabled={isChecked || handoffLoading || !!answerImageId}
                    className="rounded-md border border-chem-teal bg-chem-teal-soft px-3 py-1.5 text-sm text-chem-teal-dark hover:border-chem-teal disabled:opacity-60"
                  >
                    {handoffLoading
                      ? "Создание QR…"
                      : "Сфотографировать с телефона"}
                  </button>
                  <label className="cursor-pointer rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-700 hover:border-zinc-400">
                    {uploadingAnswerImage ? "Загрузка…" : "Прикрепить с этого устройства"}
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      className="sr-only"
                      disabled={isChecked || uploadingAnswerImage}
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          void handleAnswerImageUpload(file);
                        }
                        e.target.value = "";
                      }}
                    />
                  </label>
                </div>

                {handoffUrl ? (
                  <div className="flex flex-col items-start gap-2 rounded-lg border border-zinc-200 bg-zinc-50 p-3">
                    <p className="text-xs text-zinc-600">
                      Отсканируйте QR на телефоне. Фото появится здесь автоматически.
                    </p>
                    <QRCode value={handoffUrl} size={128} />
                    {handoffPolling ? (
                      <p className="text-xs text-zinc-500">Ожидание фото с телефона…</p>
                    ) : null}
                  </div>
                ) : null}

                {answerImageUrl || photoReceivedFromPhone ? (
                  <span className="text-xs text-chem-teal-dark">
                    {photoReceivedFromPhone ? "Фото получено с телефона" : "Фото прикреплено"}
                  </span>
                ) : (
                  <span className="text-xs text-zinc-500">
                    Фото обязательно перед сравнением
                  </span>
                )}
              </div>
            ) : null}
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

          {isChecked && !isSelfCheck ? (
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

          {isChecked && isSelfCheck ? (
            <p
              role="status"
              aria-live="polite"
              className="mt-4 px-3 py-2 text-sm bg-chem-teal-soft text-chem-teal-dark"
            >
              Ответ сохранён. Сравните с эталоном ниже.
            </p>
          ) : null}

          {referenceAnswer ? (
            <div className="mt-4 rounded-lg border border-zinc-200 bg-zinc-50 p-4">
              <p className="mb-2 text-sm font-medium text-zinc-700">
                Эталонный ответ
              </p>
              <CustomQuestionContent blocks={referenceAnswer} />
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
              onClick={isSelfCheck ? handleCompare : handleCheck}
              disabled={actionDisabled}
              className="chem-btn-primary min-h-[44px] flex-1 px-4 py-2.5 text-sm disabled:opacity-60 sm:flex-none sm:px-5"
            >
              {checking
                ? "Обработка…"
                : isSelfCheck
                  ? "Сравнить ответ"
                  : "Проверить"}
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
              {customSession && scorableCount < steps.length
                ? `Проверено ${checkedCount} из ${steps.length} (в баллах: ${scorableCount})`
                : `Проверено ${checkedCount} из ${steps.length}`}
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
