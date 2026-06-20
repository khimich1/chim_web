"use client";

import { useEffect, useState } from "react";

import { AuthenticatedAudio } from "@/components/homework/AuthenticatedAudio";
import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";
import { getStudentHomeworkFeedback } from "@/lib/api/homework-feedback";
import { formatFetchError } from "@/lib/api/client";
import type { StudentHomeworkFeedback } from "@/lib/api/types";

export function HomeworkFeedbackPanel({ homeworkId }: { homeworkId: string }) {
  const [feedback, setFeedback] = useState<StudentHomeworkFeedback | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
                <ul className="mt-2 flex flex-wrap gap-2">
                  {step.teacher_image_urls.map((url, index) => (
                    <li key={url}>
                      <AuthenticatedImage
                        src={url}
                        alt={`Фото разбора ${index + 1}`}
                        className="h-24 w-24 rounded object-cover"
                      />
                    </li>
                  ))}
                </ul>
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
            <ul className="mt-2 flex flex-wrap gap-2">
              {feedback.submission.teacher_image_urls.map((url, index) => (
                <li key={url}>
                  <AuthenticatedImage
                    src={url}
                    alt={`Фото общего комментария ${index + 1}`}
                    className="h-24 w-24 rounded object-cover"
                  />
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
