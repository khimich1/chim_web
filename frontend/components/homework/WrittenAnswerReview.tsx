"use client";

import { CustomQuestionContent } from "@/components/tests/CustomQuestionContent";
import { ImageViewer } from "@/components/homework/ImageViewer";
import type { HomeworkSubmissionStep } from "@/lib/api/types";

export function WrittenAnswerReview({
  steps,
}: {
  steps: HomeworkSubmissionStep[];
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
          </li>
        ))}
      </ul>
    </div>
  );
}
