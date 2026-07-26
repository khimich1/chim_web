"use client";

import { useCallback, useState } from "react";

import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";
import {
  ImageLightbox,
  type LightboxItem,
} from "@/components/common/ImageLightbox";
import type { HomeworkSubmissionStep } from "@/lib/api/types";

export function HomeworkSubmissionPhotos({
  steps,
}: {
  steps: HomeworkSubmissionStep[];
}) {
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxItems, setLightboxItems] = useState<LightboxItem[]>([]);
  const [lightboxIndex, setLightboxIndex] = useState(0);

  const openLightbox = useCallback((items: LightboxItem[], index: number) => {
    if (items.length === 0) {
      return;
    }
    setLightboxItems(items);
    setLightboxIndex(index);
    setLightboxOpen(true);
  }, []);

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
        {photoSteps.map((step) => {
          const items: LightboxItem[] = step.answer_image_urls.map(
            (url, index) => ({
              src: url,
              alt: `Фото ответа к заданию ${step.position + 1}, страница ${index + 1}`,
            }),
          );

          return (
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
                {items.map((item, index) => (
                  <li key={item.src}>
                    <button
                      type="button"
                      onClick={() => openLightbox(items, index)}
                      className="block w-full cursor-zoom-in text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-400"
                      aria-label={`Открыть ${item.alt}`}
                    >
                      <AuthenticatedImage
                        src={item.src}
                        alt={item.alt}
                        className="max-h-64 rounded-md border border-zinc-200 object-contain"
                      />
                    </button>
                  </li>
                ))}
              </ul>
            </li>
          );
        })}
      </ul>

      <ImageLightbox
        open={lightboxOpen}
        items={lightboxItems}
        index={lightboxIndex}
        onClose={() => setLightboxOpen(false)}
        onIndexChange={setLightboxIndex}
      />
    </div>
  );
}
