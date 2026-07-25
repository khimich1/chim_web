"use client";

import { useCallback, useState } from "react";

import {
  ImageLightbox,
  type LightboxItem,
} from "@/components/common/ImageLightbox";
import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";
import { AuthenticatedAudio } from "@/components/homework/AuthenticatedAudio";
import { ImageViewer } from "@/components/homework/ImageViewer";
import { StepFeedbackForm } from "@/components/homework/StepFeedbackForm";
import { CustomQuestionContent } from "@/components/tests/CustomQuestionContent";
import type {
  HomeworkSubmissionStep,
  StepFeedbackContent,
} from "@/lib/api/types";

export function WrittenAnswerReview({
  homeworkId,
  steps,
  submissionFeedback,
}: {
  homeworkId: string;
  steps: HomeworkSubmissionStep[];
  submissionFeedback?: StepFeedbackContent | null;
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

  const closeLightbox = useCallback(() => {
    setLightboxOpen(false);
  }, []);

  const reviewSteps = steps.filter(
    (step) =>
      step.grading_mode === "self_check" &&
      (step.answer_image_urls?.length ?? 0) > 0,
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
        {reviewSteps.map((step) => {
          const answerItems: LightboxItem[] = step.answer_image_urls.map(
            (url, index) => ({
              src: url,
              alt: `Фото ответа к заданию ${step.position + 1}, страница ${index + 1}`,
            }),
          );

          return (
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
                  <CustomQuestionContent
                    blocks={step.question_blocks}
                    onImageClick={openLightbox}
                  />
                </div>
              ) : null}

              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div>
                  <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
                    Ответ ученика
                  </p>
                  <ul className="flex flex-col gap-3">
                    {step.answer_image_urls.map((url, index) => (
                      <li key={url}>
                        {step.answer_image_urls.length > 1 ? (
                          <p className="mb-1 text-xs text-zinc-500">
                            Страница {index + 1}
                          </p>
                        ) : null}
                        <ImageViewer
                          src={url}
                          alt={answerItems[index]?.alt ?? `Фото ответа ${index + 1}`}
                          onExpand={() => openLightbox(answerItems, index)}
                        />
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
                    Эталон
                  </p>
                  <div className="rounded-md border border-zinc-200 bg-white p-3">
                    {step.reference_answer && step.reference_answer.length > 0 ? (
                      <CustomQuestionContent
                        blocks={step.reference_answer}
                        onImageClick={openLightbox}
                      />
                    ) : (
                      <p className="text-sm text-zinc-500">Эталон не задан</p>
                    )}
                  </div>
                </div>
              </div>

              {step.feedback ? (
                <SavedFeedbackPreview
                  feedback={step.feedback}
                  onImageClick={openLightbox}
                />
              ) : null}

              <StepFeedbackForm
                homeworkId={homeworkId}
                position={step.position}
                title={`Разбор: ${step.title ?? `задание ${step.position + 1}`}`}
                initial={step.feedback}
              />
            </li>
          );
        })}
      </ul>

      <div className="mt-6 rounded-lg border border-zinc-200 p-4">
        <h3 className="text-sm font-medium text-zinc-800">
          Общий комментарий к сдаче
        </h3>
        {submissionFeedback ? (
          <div className="mt-3">
            <SavedFeedbackPreview
              feedback={submissionFeedback}
              onImageClick={openLightbox}
            />
          </div>
        ) : null}
        <StepFeedbackForm
          homeworkId={homeworkId}
          title="Общий комментарий (опционально)"
          initial={submissionFeedback}
        />
      </div>

      <ImageLightbox
        open={lightboxOpen}
        items={lightboxItems}
        index={lightboxIndex}
        onClose={closeLightbox}
        onIndexChange={setLightboxIndex}
      />
    </div>
  );
}

function SavedFeedbackPreview({
  feedback,
  onImageClick,
}: {
  feedback: StepFeedbackContent;
  onImageClick: (items: LightboxItem[], index: number) => void;
}) {
  const items: LightboxItem[] = feedback.teacher_image_urls.map((url, index) => ({
    src: url,
    alt: `Фото разбора ${index + 1}`,
  }));

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
      {items.length > 0 ? (
        <ul className="mt-2 flex flex-wrap gap-2">
          {items.map((item, index) => (
            <li key={item.src}>
              <button
                type="button"
                onClick={() => onImageClick(items, index)}
                className="cursor-zoom-in rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-400"
                aria-label={`Открыть фото разбора ${index + 1}`}
              >
                <AuthenticatedImage
                  src={item.src}
                  alt={item.alt}
                  className="h-20 w-20 rounded object-cover"
                />
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
