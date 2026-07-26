"use client";

import { useCallback, useEffect, useState } from "react";
import QRCode from "react-qr-code";

import { AuthenticatedAudio } from "@/components/homework/AuthenticatedAudio";
import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";
import {
  ImageLightbox,
  type LightboxItem,
} from "@/components/common/ImageLightbox";
import { VoiceRecorder } from "@/components/homework/VoiceRecorder";
import { saveStepFeedback, saveSubmissionFeedback } from "@/lib/api/homework-feedback";
import { createFeedbackHandoff, getCaptureMeta } from "@/lib/api/handoff";
import { uploadAudio, uploadImage } from "@/lib/api/uploads";
import type { StepFeedbackContent, StepFeedbackInput } from "@/lib/api/types";
import { ApiError, formatFetchError } from "@/lib/api/client";
import {
  IMAGE_INTAKE_HINT,
  imageFilesFromDataTransfer,
  isAllowedImageFile,
} from "@/lib/image-intake";

const FEEDBACK_IMAGE_LIMIT = 5;
const FEEDBACK_IMAGE_CLASS =
  "my-2 block h-auto max-h-64 w-full max-w-full rounded-md border border-zinc-200 object-contain";

type FeedbackFormProps = {
  homeworkId: string;
  position?: number;
  title: string;
  initial?: StepFeedbackContent | null;
  onSaved?: (feedback: StepFeedbackContent) => void;
};

export function StepFeedbackForm({
  homeworkId,
  position,
  title,
  initial,
  onSaved,
}: FeedbackFormProps) {
  const [teacherText, setTeacherText] = useState(initial?.teacher_text ?? "");
  const [voiceId, setVoiceId] = useState<string | null>(
    initial?.teacher_voice_url
      ? initial.teacher_voice_url.split("/").pop() ?? null
      : null,
  );
  const [voiceUrl, setVoiceUrl] = useState<string | null>(
    initial?.teacher_voice_url ?? null,
  );
  const [imageIds, setImageIds] = useState<string[]>(
    (initial?.teacher_image_urls ?? []).map((url) => url.split("/").pop()!).filter(Boolean),
  );
  const [imageUrls, setImageUrls] = useState<string[]>(
    initial?.teacher_image_urls ?? [],
  );
  const [saving, setSaving] = useState(false);
  const [uploadingVoice, setUploadingVoice] = useState(false);
  const [uploadingImages, setUploadingImages] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const [handoffUrl, setHandoffUrl] = useState<string | null>(null);
  const [handoffToken, setHandoffToken] = useState<string | null>(null);
  const [handoffLoading, setHandoffLoading] = useState(false);
  const [handoffPolling, setHandoffPolling] = useState(false);
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

  const hasContent =
    teacherText.trim().length > 0 || Boolean(voiceId) || imageIds.length > 0;
  const slotsLeft = FEEDBACK_IMAGE_LIMIT - imageIds.length;
  const intakeDisabled =
    slotsLeft <= 0 || saving || uploadingImages || uploadingVoice;
  const draftLightboxItems: LightboxItem[] = imageUrls.map((url, index) => ({
    src: url,
    alt: `Фото разбора ${index + 1}`,
  }));

  const handleVoiceRecorded = async (file: File, durationSec: number) => {
    setUploadingVoice(true);
    setError(null);
    try {
      const uploaded = await uploadAudio(file, durationSec);
      setVoiceId(uploaded.id);
      setVoiceUrl(uploaded.url);
    } catch (err) {
      setError(formatFetchError(err, "Не удалось загрузить аудио"));
    } finally {
      setUploadingVoice(false);
    }
  };

  const uploadFeedbackImages = async (
    files: File[],
    truncated = false,
  ) => {
    if (files.length === 0 || intakeDisabled) {
      return;
    }
    const toUpload = files.slice(0, slotsLeft);
    setError(null);
    setUploadingImages(true);
    try {
      for (const file of toUpload) {
        if (!isAllowedImageFile(file)) {
          setError("Формат не поддерживается. Используйте JPEG, PNG или WebP.");
          continue;
        }
        const uploaded = await uploadImage(file);
        setImageIds((prev) => [...prev, uploaded.id]);
        setImageUrls((prev) => [...prev, uploaded.url]);
      }
      if (truncated || files.length > toUpload.length) {
        setError(
          `Можно прикрепить не более ${FEEDBACK_IMAGE_LIMIT} фото; лишние отброшены.`,
        );
      }
    } catch (err) {
      setError(formatFetchError(err, "Не удалось загрузить фото"));
    } finally {
      setUploadingImages(false);
    }
  };

  const handleImageSelected = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) {
      return;
    }
    await uploadFeedbackImages([file]);
  };

  const handlePaste = (event: React.ClipboardEvent) => {
    if (intakeDisabled) {
      return;
    }
    const { files, truncated } = imageFilesFromDataTransfer(
      event.clipboardData,
      { limit: slotsLeft },
    );
    if (files.length === 0) {
      return;
    }
    event.preventDefault();
    void uploadFeedbackImages(files, truncated);
  };

  const handleDragOver = (event: React.DragEvent) => {
    if (intakeDisabled) {
      return;
    }
    const { files } = imageFilesFromDataTransfer(event.dataTransfer, {
      limit: slotsLeft,
    });
    if (files.length === 0) {
      return;
    }
    event.preventDefault();
  };

  const handleDrop = (event: React.DragEvent) => {
    if (intakeDisabled) {
      return;
    }
    const { files, truncated } = imageFilesFromDataTransfer(
      event.dataTransfer,
      { limit: slotsLeft },
    );
    if (files.length === 0) {
      return;
    }
    event.preventDefault();
    void uploadFeedbackImages(files, truncated);
  };

  const removeImage = (index: number) => {
    setImageIds((prev) => prev.filter((_, i) => i !== index));
    setImageUrls((prev) => prev.filter((_, i) => i !== index));
  };

  const clearHandoff = useCallback(() => {
    setHandoffUrl(null);
    setHandoffToken(null);
    setHandoffPolling(false);
  }, []);

  const pollHandoffPhoto = useCallback(async () => {
    if (!handoffToken) {
      return;
    }
    try {
      const meta = await getCaptureMeta(handoffToken);
      if (!meta.staged_image_id || !meta.staged_image_url) {
        return;
      }
      const stagedId = meta.staged_image_id;
      const stagedUrl = meta.staged_image_url;
      setImageIds((prev) => {
        if (prev.includes(stagedId) || prev.length >= FEEDBACK_IMAGE_LIMIT) {
          return prev;
        }
        return [...prev, stagedId];
      });
      setImageUrls((prev) => {
        if (prev.includes(stagedUrl) || prev.length >= FEEDBACK_IMAGE_LIMIT) {
          return prev;
        }
        return [...prev, stagedUrl];
      });
      // Always clear QR after a staged photo is seen (fits or not) — avoid stuck "Ожидание…".
      clearHandoff();
    } catch (err) {
      if (
        err instanceof ApiError &&
        (err.status === 410 || err.status === 404)
      ) {
        clearHandoff();
        setError(
          err.status === 410
            ? "Ссылка для съёмки истекла. Создайте QR снова."
            : "Ссылка для съёмки недействительна. Создайте QR снова.",
        );
      }
      // other errors: best-effort until photo arrives or handoff expires
    }
  }, [handoffToken, clearHandoff]);

  useEffect(() => {
    if (slotsLeft <= 0 && (handoffUrl || handoffToken || handoffPolling)) {
      clearHandoff();
    }
  }, [slotsLeft, handoffUrl, handoffToken, handoffPolling, clearHandoff]);

  useEffect(() => {
    if (!handoffPolling || !handoffToken || slotsLeft <= 0) {
      return;
    }
    const intervalId = window.setInterval(() => {
      void pollHandoffPhoto();
    }, 2500);
    void pollHandoffPhoto();
    return () => window.clearInterval(intervalId);
  }, [handoffPolling, handoffToken, slotsLeft, pollHandoffPhoto]);

  const handleStartHandoff = async () => {
    if (intakeDisabled) {
      return;
    }
    setError(null);
    setHandoffLoading(true);
    try {
      const result = await createFeedbackHandoff(homeworkId, position ?? null);
      setHandoffUrl(result.capture_url);
      setHandoffToken(result.token);
      setHandoffPolling(true);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : formatFetchError(err, "Не удалось создать QR для съёмки."),
      );
    } finally {
      setHandoffLoading(false);
    }
  };

  const buildPayload = (): StepFeedbackInput => ({
    teacher_text: teacherText.trim() || null,
    teacher_voice_id: voiceId,
    teacher_image_ids: imageIds,
  });

  const handleSave = async () => {
    if (!hasContent) {
      setError("Добавьте текст, голос или фото");
      return;
    }

    setSaving(true);
    setError(null);
    setSavedMessage(null);

    try {
      const payload = buildPayload();
      if (position === undefined) {
        const saved = await saveSubmissionFeedback(homeworkId, payload);
        onSaved?.(saved);
      } else {
        const saved = await saveStepFeedback(homeworkId, position, payload);
        onSaved?.({
          teacher_text: saved.teacher_text,
          teacher_voice_url: saved.teacher_voice_url,
          teacher_image_urls: saved.teacher_image_urls,
          published_at: saved.published_at,
        });
      }
      setSavedMessage("Разбор сохранён");
    } catch (err) {
      setError(formatFetchError(err, "Не удалось сохранить разбор"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mt-4 rounded-md border border-dashed border-zinc-300 bg-zinc-50 p-4">
      <h3 className="text-sm font-medium text-zinc-800">{title}</h3>

      <div className="mt-3 rounded-lg border border-zinc-200 bg-white p-3 shadow-sm">
        <div className="flex items-start gap-2">
          <textarea
            className="chem-input min-h-[140px] w-full flex-1 resize-y border-0 bg-transparent p-0 text-sm shadow-none focus:ring-0"
            value={teacherText}
            onChange={(event) => setTeacherText(event.target.value)}
            maxLength={4000}
            placeholder="Что исправить, на что обратить внимание…"
            aria-label="Комментарий к разбору"
          />
          {voiceUrl ? null : (
            <div className="shrink-0 pt-0.5">
              <VoiceRecorder
                variant="icon"
                onRecorded={(file, durationSec) =>
                  void handleVoiceRecorded(file, durationSec)
                }
                disabled={uploadingVoice || saving}
              />
            </div>
          )}
        </div>
        {voiceUrl ? (
          <div className="mt-2 space-y-2 border-t border-zinc-100 pt-2">
            <AuthenticatedAudio src={voiceUrl} className="w-full" />
            <button
              type="button"
              className="chem-btn-secondary text-sm"
              onClick={() => {
                setVoiceId(null);
                setVoiceUrl(null);
              }}
            >
              Удалить голос
            </button>
          </div>
        ) : null}
      </div>

      <div
        className="mt-3"
        data-testid="feedback-image-intake"
        onPaste={handlePaste}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <p className="text-xs text-zinc-500">{IMAGE_INTAKE_HINT}</p>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => void handleStartHandoff()}
            disabled={intakeDisabled || handoffLoading}
            className="rounded-md border border-chem-teal bg-chem-teal-soft px-3 py-1.5 text-sm text-chem-teal-dark hover:border-chem-teal disabled:opacity-60"
          >
            {handoffLoading
              ? "Создание QR…"
              : "Сфотографировать с телефона"}
          </button>
          <label className="cursor-pointer rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-700 hover:border-zinc-400 has-[:disabled]:cursor-not-allowed has-[:disabled]:opacity-60">
            {uploadingImages ? "Загрузка…" : "Прикрепить с этого устройства"}
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="sr-only"
              onChange={(event) => void handleImageSelected(event)}
              disabled={intakeDisabled}
            />
          </label>
        </div>

        {handoffUrl ? (
          <div className="mt-2 flex flex-col items-start gap-2 rounded-lg border border-zinc-200 bg-zinc-50 p-3">
            <p className="text-xs text-zinc-600">
              Отсканируйте QR на телефоне. Фото появится здесь автоматически.
            </p>
            <QRCode value={handoffUrl} size={128} />
            {handoffPolling ? (
              <p className="text-xs text-zinc-500">Ожидание фото с телефона…</p>
            ) : null}
          </div>
        ) : null}

        {slotsLeft <= 0 ? (
          <p className="mt-1 text-xs text-zinc-500" role="status">
            Достигнут лимит {FEEDBACK_IMAGE_LIMIT} фото.
          </p>
        ) : null}
        {draftLightboxItems.length > 0 ? (
          <ul className="mt-2 flex flex-col gap-3">
            {draftLightboxItems.map((item, index) => (
              <li key={item.src} className="relative">
                <button
                  type="button"
                  onClick={() => openLightbox(draftLightboxItems, index)}
                  className="block w-full cursor-zoom-in text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-400"
                  aria-label={`Открыть ${item.alt}`}
                >
                  <AuthenticatedImage
                    src={item.src}
                    alt={item.alt}
                    className={FEEDBACK_IMAGE_CLASS}
                  />
                </button>
                <button
                  type="button"
                  className="absolute right-1 top-1 rounded-full bg-zinc-800 px-1.5 text-xs text-white"
                  onClick={() => removeImage(index)}
                  aria-label="Удалить фото"
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      {error ? (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
      {savedMessage ? (
        <p className="mt-3 text-sm text-[var(--text-positive)]" role="status">
          {savedMessage}
        </p>
      ) : null}

      <div className="mt-4 flex justify-end">
        <button
          type="button"
          className="chem-btn-primary rounded-full px-5 py-2 text-sm font-semibold"
          onClick={() => void handleSave()}
          disabled={saving || uploadingVoice || uploadingImages || !hasContent}
        >
          {saving ? "Сохранение…" : "Сохранить"}
        </button>
      </div>

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
