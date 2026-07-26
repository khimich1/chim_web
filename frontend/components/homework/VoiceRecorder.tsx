"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const WARN_DURATION_SEC = 600;

function MicIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  );
}

export function VoiceRecorder({
  onRecorded,
  disabled = false,
  variant = "button",
}: {
  onRecorded: (file: File, durationSec: number) => void;
  disabled?: boolean;
  variant?: "button" | "icon";
}) {
  const [recording, setRecording] = useState(false);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewFile, setPreviewFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [warnLongRecording, setWarnLongRecording] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const cleanupStream = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    mediaRecorderRef.current = null;
  }, []);

  useEffect(() => {
    return () => {
      cleanupStream();
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [cleanupStream, previewUrl]);

  const startRecording = async () => {
    setError(null);
    setWarnLongRecording(false);
    setPreviewUrl(null);
    setPreviewFile(null);
    chunksRef.current = [];

    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Запись голоса не поддерживается в этом браузере");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "audio/ogg";
      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        const extension = mimeType === "audio/webm" ? "webm" : "ogg";
        const file = new File([blob], `feedback.${extension}`, { type: mimeType });
        const url = URL.createObjectURL(blob);
        setPreviewUrl(url);
        setPreviewFile(file);
        cleanupStream();
      };

      recorder.start();
      setRecording(true);
      setElapsedSec(0);
      timerRef.current = setInterval(() => {
        setElapsedSec((value) => {
          const next = value + 1;
          if (next >= WARN_DURATION_SEC) {
            setWarnLongRecording(true);
          }
          return next;
        });
      }, 1000);
    } catch {
      setError("Не удалось получить доступ к микрофону");
      cleanupStream();
    }
  };

  const stopRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
    setRecording(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const confirmRecording = () => {
    if (previewFile) {
      onRecorded(previewFile, elapsedSec);
    }
  };

  const discardRecording = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setPreviewFile(null);
    setElapsedSec(0);
    setWarnLongRecording(false);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        {!recording && !previewFile ? (
          variant === "icon" ? (
            <button
              type="button"
              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-zinc-300 bg-white text-zinc-700 hover:border-zinc-400 hover:bg-zinc-50 disabled:opacity-60"
              onClick={() => void startRecording()}
              disabled={disabled}
              aria-label="Записать голос"
            >
              <MicIcon className="h-4 w-4" />
            </button>
          ) : (
            <button
              type="button"
              className="chem-btn-secondary text-sm"
              onClick={() => void startRecording()}
              disabled={disabled}
            >
              Записать голос
            </button>
          )
        ) : null}

        {recording ? (
          <>
            <button
              type="button"
              className="chem-btn-primary text-sm"
              onClick={stopRecording}
            >
              Остановить
            </button>
            <span className="text-sm text-red-600" aria-live="polite">
              ● {formatTime(elapsedSec)}
            </span>
          </>
        ) : null}
      </div>

      {warnLongRecording ? (
        <p className="text-sm text-amber-700" role="alert">
          Запись дольше 10 минут — сервер может отклонить загрузку.
        </p>
      ) : null}

      {error ? (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}

      {previewUrl ? (
        <div className="space-y-2 rounded-md border border-zinc-200 p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
            Превью записи ({formatTime(elapsedSec)})
          </p>
          <audio src={previewUrl} controls className="w-full">
            <track kind="captions" />
          </audio>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="chem-btn-primary text-sm"
              onClick={confirmRecording}
            >
              Использовать запись
            </button>
            <button
              type="button"
              className="chem-btn-secondary text-sm"
              onClick={discardRecording}
            >
              Перезаписать
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
