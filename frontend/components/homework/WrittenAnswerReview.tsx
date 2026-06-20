"use client";

import { CustomQuestionContent } from "@/components/tests/CustomQuestionContent";
import { ImageViewer } from "@/components/homework/ImageViewer";
import { StepFeedbackForm } from "@/components/homework/StepFeedbackForm";
import { AuthenticatedAudio } from "@/components/homework/AuthenticatedAudio";
import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";
import type { HomeworkSubmissionStep, StepFeedbackContent } from "@/lib/api/types";

export function WrittenAnswerReview({
  homeworkId,
  steps,
  submissionFeedback,
}: {
  homeworkId: string;
  steps: HomeworkSubmissionStep[];
  submissionFeedback?: StepFeedbackContent | null;
}) {
  const reviewSteps = steps.filter(
    (step) => step.answer_image_url && step.grading_mode === "self_check",
  );

  if (reviewSteps.length === 0) {
    return null;
  }

  return (
    <div className="mt-6 border-t border-zinc-200 pt-4">
      <h2 className="text-sm font-medium text-zinc-700">
        Проверка письменных ответов
      </h2>
      <ul className="mt-3 flex flex-col gap-6">
        {reviewSteps.map((step) => (
          <li
            key={step.position}
            className="rounded-lg border border-zinc-200 p-4"
          >
            <p className="text-sm font-medium text-zinc-800">
              {step.title ?? `Задание ${step.position + 1}`}
              {step.answer ? (
                <span className="ml-2 font-normal text-zinc-500">
                  — {step.answer}
                </span>
              ) : null}
            </p>

            {step.question_blocks && step.question_blocks.length > 0 ? (
              <div className="mt-3 rounded-md bg-zinc-50 p-3">
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
                  Условие
                </p>
                <CustomQuestionContent blocks={step.question_blocks} />
              </div>
            ) : null}

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
                  Ответ ученика
                </p>
                <ImageViewer
                  src={step.answer_image_url!}
                  alt={`Фото ответа к заданию ${step.position + 1}`}
                />
              </div>
              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
                  Эталон
                </p>
                <div className="rounded-md border border-zinc-200 bg-white p-3">
                  {step.reference_answer && step.reference_answer.length > 0 ? (
                    <CustomQuestionContent blocks={step.reference_answer} />
                  ) : (
                    <p className="text-sm text-zinc-500">Эталон не задан</p>
                  )}
                </div>
              </div>
            </div>

            {step.feedback ? (
              <SavedFeedbackPreview feedback={step.feedback} />
            ) : null}

            <StepFeedbackForm
              homeworkId={homeworkId}
              position={step.position}
              title={`Разбор: ${step.title ?? `задание ${step.position + 1}`}`}
              initial={step.feedback}
            />
          </li>
        ))}
      </ul>

      <div className="mt-6 rounded-lg border border-zinc-200 p-4">
        <h3 className="text-sm font-medium text-zinc-800">Общий комментарий к сдаче</h3>
        {submissionFeedback ? (
          <div className="mt-3">
            <SavedFeedbackPreview feedback={submissionFeedback} />
          </div>
        ) : null}
        <StepFeedbackForm
          homeworkId={homeworkId}
          title="Общий комментарий (опционально)"
          initial={submissionFeedback}
        />
      </div>
    </div>
  );
}

function SavedFeedbackPreview({ feedback }: { feedback: StepFeedbackContent }) {
  return (
    <div className="mt-4 rounded-md border border-chem-green/30 bg-chem-green/5 p-3">
      <p className="text-xs font-medium uppercase tracking-wide text-chem-green">
        Сохранённый разбор
      </p>
      {feedback.teacher_text ? (
        <p className="mt-2 text-sm text-zinc-800">{feedback.teacher_text}</p>
      ) : null}
      {feedback.teacher_voice_url ? (
        <div className="mt-2">
          <AuthenticatedAudio src={feedback.teacher_voice_url} className="w-full" />
        </div>
      ) : null}
      {feedback.teacher_image_urls.length > 0 ? (
        <ul className="mt-2 flex flex-wrap gap-2">
          {feedback.teacher_image_urls.map((url, index) => (
            <li key={url}>
              <AuthenticatedImage
                src={url}
                alt={`Фото разбора ${index + 1}`}
                className="h-20 w-20 rounded object-cover"
              />
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
