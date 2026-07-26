"use client";

import { useCallback, useEffect, useState } from "react";

import { AuthenticatedAudio } from "@/components/homework/AuthenticatedAudio";
import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";
import {
  ImageLightbox,
  type LightboxItem,
} from "@/components/common/ImageLightbox";
import { getStudentHomeworkFeedback } from "@/lib/api/homework-feedback";
import { formatFetchError } from "@/lib/api/client";
import type { StudentHomeworkFeedback } from "@/lib/api/types";

function FeedbackImageThumbs({
  urls,
  altPrefix,
  onOpen,
}: {
  urls: string[];
  altPrefix: string;
  onOpen: (items: LightboxItem[], index: number) => void;
}) {
  const items: LightboxItem[] = urls.map((url, index) => ({
    src: url,
    alt: `${altPrefix} ${index + 1}`,
  }));

  return (
    <ul className="mt-2 flex flex-wrap gap-2">
      {items.map((item, index) => (
        <li key={item.src}>
          <button
            type="button"
            onClick={() => onOpen(items, index)}
            className="cursor-zoom-in rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-400"
            aria-label={`Открыть ${item.alt}`}
          >
            <AuthenticatedImage
              src={item.src}
              alt={item.alt}
              className="h-24 w-24 rounded object-cover"
            />
          </button>
        </li>
      ))}
    </ul>
  );
}

export function HomeworkFeedbackPanel({ homeworkId }: { homeworkId: string }) {
  const [feedback, setFeedback] = useState<StudentHomeworkFeedback | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getStudentHomeworkFeedback(homeworkId);
        if (!cancelled) {
          setFeedback(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(formatFetchError(err, "Не удалось загрузить разбор"));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [homeworkId]);

  if (loading) {
    return (
      <p className="text-sm text-zinc-500" aria-live="polite">
        Загрузка разбора…
      </p>
    );
  }

  if (error) {
    return (
      <p className="text-sm text-red-600" role="alert">
        {error}
      </p>
    );
  }

  if (!feedback?.has_feedback) {
    return null;
  }

  return (
    <section
      className="chem-card mt-8 rounded-lg p-6"
      aria-labelledby="teacher-feedback-heading"
    >
      <h2 id="teacher-feedback-heading" className="text-lg font-semibold text-zinc-900">
        Разбор преподавателя
      </h2>

      {feedback.steps.length > 0 ? (
        <ul className="mt-4 flex flex-col gap-4">
          {feedback.steps.map((step) => (
            <li
              key={step.position}
              className="rounded-md border border-zinc-200 p-4"
            >
              <h3 className="text-sm font-medium text-zinc-800">
                {step.title ?? `Задание ${step.position + 1}`}
              </h3>
              {step.teacher_text ? (
                <p className="mt-2 text-sm text-zinc-700">{step.teacher_text}</p>
              ) : null}
              {step.teacher_voice_url ? (
                <div className="mt-2">
                  <AuthenticatedAudio
                    src={step.teacher_voice_url}
                    className="w-full"
                  />
                </div>
              ) : null}
              {step.teacher_image_urls.length > 0 ? (
                <FeedbackImageThumbs
                  urls={step.teacher_image_urls}
                  altPrefix="Фото разбора"
                  onOpen={openLightbox}
                />
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}

      {feedback.submission ? (
        <div className="mt-4 rounded-md border border-zinc-200 bg-zinc-50 p-4">
          <h3 className="text-sm font-medium text-zinc-800">Общий комментарий</h3>
          {feedback.submission.teacher_text ? (
            <p className="mt-2 text-sm text-zinc-700">
              {feedback.submission.teacher_text}
            </p>
          ) : null}
          {feedback.submission.teacher_voice_url ? (
            <div className="mt-2">
              <AuthenticatedAudio
                src={feedback.submission.teacher_voice_url}
                className="w-full"
              />
            </div>
          ) : null}
          {feedback.submission.teacher_image_urls.length > 0 ? (
            <FeedbackImageThumbs
              urls={feedback.submission.teacher_image_urls}
              altPrefix="Фото общего комментария"
              onOpen={openLightbox}
            />
          ) : null}
        </div>
      ) : null}

      <ImageLightbox
        open={lightboxOpen}
        items={lightboxItems}
        index={lightboxIndex}
        onClose={() => setLightboxOpen(false)}
        onIndexChange={setLightboxIndex}
      />
    </section>
  );
}
