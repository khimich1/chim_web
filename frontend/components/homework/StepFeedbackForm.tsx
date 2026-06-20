"use client";

import { useState } from "react";

import { AuthenticatedAudio } from "@/components/homework/AuthenticatedAudio";
import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";
import { VoiceRecorder } from "@/components/homework/VoiceRecorder";
import { saveStepFeedback, saveSubmissionFeedback } from "@/lib/api/homework-feedback";
import { uploadAudio, uploadImage } from "@/lib/api/uploads";
import type { StepFeedbackContent, StepFeedbackInput } from "@/lib/api/types";
import { formatFetchError } from "@/lib/api/client";

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
  const [error, setError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  const hasContent =
    teacherText.trim().length > 0 || Boolean(voiceId) || imageIds.length > 0;

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

  const handleImageSelected = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || imageIds.length >= 5) {
      return;
    }
    setError(null);
    try {
      const uploaded = await uploadImage(file);
      setImageIds((prev) => [...prev, uploaded.id]);
      setImageUrls((prev) => [...prev, uploaded.url]);
    } catch (err) {
      setError(formatFetchError(err, "Не удалось загрузить фото"));
    }
  };

  const removeImage = (index: number) => {
    setImageIds((prev) => prev.filter((_, i) => i !== index));
    setImageUrls((prev) => prev.filter((_, i) => i !== index));
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

      <label className="mt-3 block text-sm text-zinc-700">
        Текстовый комментарий
        <textarea
          className="chem-input mt-1 min-h-[80px] w-full"
          value={teacherText}
          onChange={(event) => setTeacherText(event.target.value)}
          maxLength={4000}
          placeholder="Что исправить, на что обратить внимание…"
        />
      </label>

      <div className="mt-3">
        <p className="text-sm font-medium text-zinc-700">Голосовой комментарий</p>
        {voiceUrl ? (
          <div className="mt-2 space-y-2">
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
        ) : (
          <div className="mt-2">
            <VoiceRecorder
              onRecorded={(file, durationSec) => void handleVoiceRecorded(file, durationSec)}
              disabled={uploadingVoice || saving}
            />
          </div>
        )}
      </div>

      <div className="mt-3">
        <p className="text-sm font-medium text-zinc-700">Фото к разбору</p>
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="mt-2 block text-sm"
          onChange={(event) => void handleImageSelected(event)}
          disabled={imageIds.length >= 5 || saving}
        />
        {imageUrls.length > 0 ? (
          <ul className="mt-2 flex flex-wrap gap-2">
            {imageUrls.map((url, index) => (
              <li key={url} className="relative">
                <AuthenticatedImage
                  src={url}
                  alt={`Фото разбора ${index + 1}`}
                  className="h-20 w-20 rounded object-cover"
                />
                <button
                  type="button"
                  className="absolute -right-1 -top-1 rounded-full bg-zinc-800 px-1.5 text-xs text-white"
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

      <button
        type="button"
        className="chem-btn-primary mt-4 text-sm"
        onClick={() => void handleSave()}
        disabled={saving || uploadingVoice || !hasContent}
      >
        {saving ? "Сохранение…" : "Сохранить разбор"}
      </button>
    </div>
  );
}
