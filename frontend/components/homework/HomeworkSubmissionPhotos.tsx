"use client";

import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";
import type { HomeworkSubmissionStep } from "@/lib/api/types";

export function HomeworkSubmissionPhotos({
  steps,
}: {
  steps: HomeworkSubmissionStep[];
}) {
  const photoSteps = steps.filter(
    (step) => (step.answer_image_urls?.length ?? 0) > 0,
  );

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
            <ul className="mt-2 flex flex-col gap-2">
              {step.answer_image_urls.map((url, index) => (
                <li key={url}>
                  <AuthenticatedImage
                    src={url}
                    alt={`Фото ответа к заданию ${step.position + 1}, страница ${index + 1}`}
                    className="max-h-64 rounded-md border border-zinc-200 object-contain"
                  />
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  );
}
