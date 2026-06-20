"use client";

import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";
import type { HomeworkSubmissionStep } from "@/lib/api/types";

export function HomeworkSubmissionPhotos({
  steps,
}: {
  steps: HomeworkSubmissionStep[];
}) {
  const photoSteps = steps.filter((step) => step.answer_image_url);

  if (photoSteps.length === 0) {
    return null;
  }

  return (
    <div className="mt-6 border-t border-zinc-200 pt-4">
      <h2 className="text-sm font-medium text-zinc-700">
        Фото письменных ответов
      </h2>
      <ul className="mt-3 flex flex-col gap-4">
        {photoSteps.map((step) => (
          <li key={step.position} className="rounded-lg border border-zinc-200 p-3">
            <p className="text-sm font-medium text-zinc-800">
              Задание {step.position + 1}
              {step.answer ? (
                <span className="ml-2 font-normal text-zinc-500">
                  — {step.answer}
                </span>
              ) : null}
            </p>
            {step.answer_image_url ? (
              <AuthenticatedImage
                src={step.answer_image_url}
                alt={`Фото ответа к заданию ${step.position + 1}`}
                className="mt-2 max-h-64 rounded-md border border-zinc-200 object-contain"
              />
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
