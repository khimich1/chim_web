"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import {
  CaptureChecklist,
  isCaptureChecklistComplete,
} from "@/components/homework/CaptureChecklist";
import { BrandLogo } from "@/components/ui/BrandLogo";
import { getMe } from "@/lib/api/auth";
import { ApiError, formatFetchError } from "@/lib/api/client";
import {
  captureUpload,
  getCaptureMeta,
  type CaptureMetaResponse,
} from "@/lib/api/handoff";

interface CapturePageProps {
  token: string;
}

export function CapturePage({ token }: CapturePageProps) {
  const [meta, setMeta] = useState<CaptureMetaResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [checklist, setChecklist] = useState([false, false, false]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const checklistComplete = useMemo(
    () => isCaptureChecklistComplete(checklist),
    [checklist],
  );

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [metaResult, meResult] = await Promise.allSettled([
          getCaptureMeta(token),
          getMe(),
        ]);
        if (cancelled) {
          return;
        }
        if (metaResult.status === "fulfilled") {
          setMeta(metaResult.value);
        } else {
          const err = metaResult.reason;
          setError(
            err instanceof ApiError
              ? err.message
              : "Ссылка для съёмки недействительна.",
          );
        }
        if (meResult.status === "fulfilled") {
          setAuthenticated(true);
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
  }, [token]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  function handleToggleChecklist(index: number) {
    setChecklist((prev) =>
      prev.map((value, idx) => (idx === index ? !value : value)),
    );
  }

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    event.target.value = "";
  }

  async function handleSubmit() {
    if (!selectedFile) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await captureUpload(token, selectedFile);
      setSubmitted(true);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : formatFetchError(err, "Не удалось отправить фото."),
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md items-center justify-center px-4">
        <p className="text-sm text-zinc-500">Загрузка…</p>
      </main>
    );
  }

  if (error && !meta) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-4 px-4 text-center">
        <BrandLogo size={32} />
        <p role="alert" className="text-sm text-[var(--chem-crimson)]">
          {error}
        </p>
        <Link href="/login" className="text-sm text-chem-teal underline">
          Войти
        </Link>
      </main>
    );
  }

  if (submitted) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-3 px-4 text-center">
        <BrandLogo size={32} />
        <h1 className="text-lg font-semibold text-zinc-900">Фото отправлено</h1>
        <p className="text-sm text-zinc-600">
          Вернитесь к компьютеру и нажмите «Сравнить ответ».
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-md px-4 py-8">
      <header className="mb-6 flex items-center gap-3">
        <BrandLogo size={28} />
        <div>
          <p className="text-xs uppercase tracking-wide text-zinc-500">
            Съёмка решения
          </p>
          <h1 className="text-lg font-semibold text-zinc-900">
            {meta?.task_title ?? "Задание"}
          </h1>
        </div>
      </header>

      {meta?.question_preview ? (
        <p className="mb-4 rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-700">
          {meta.question_preview}
        </p>
      ) : null}

      {!authenticated ? (
        <p className="mb-4 text-xs text-zinc-500">
          Вход не обязателен — ссылка действует ограниченное время.
          {" "}
          <Link href={`/login?redirect=/student/capture/${token}`} className="text-chem-teal underline">
            Войти
          </Link>
        </p>
      ) : null}

      <section className="chem-card rounded-xl p-4">
        <h2 className="mb-3 text-sm font-medium text-zinc-800">
          Перед съёмкой
        </h2>
        <CaptureChecklist
          checked={checklist}
          onToggle={handleToggleChecklist}
          disabled={submitting}
        />
      </section>

      <section className="mt-4 chem-card rounded-xl p-4">
        <h2 className="mb-3 text-sm font-medium text-zinc-800">Фото</h2>
        <label
          className={`flex min-h-[44px] cursor-pointer items-center justify-center rounded-md border border-dashed border-zinc-300 px-4 py-3 text-sm ${
            checklistComplete ? "text-chem-teal" : "cursor-not-allowed text-zinc-400"
          }`}
        >
          {selectedFile ? "Выбрать другое фото" : "Сфотографировать или выбрать файл"}
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            className="sr-only"
            disabled={!checklistComplete || submitting}
            onChange={handleFileChange}
          />
        </label>

        {previewUrl ? (
          <img
            src={previewUrl}
            alt="Превью фото решения"
            className="mt-4 max-h-80 w-full rounded-lg border border-zinc-200 object-contain"
          />
        ) : null}
      </section>

      {error ? (
        <p role="alert" className="mt-4 text-sm text-[var(--chem-crimson)]">
          {error}
        </p>
      ) : null}

      <button
        type="button"
        onClick={() => void handleSubmit()}
        disabled={!selectedFile || !checklistComplete || submitting}
        className="chem-btn-primary mt-6 min-h-[44px] w-full px-4 py-2.5 text-sm disabled:opacity-60"
      >
        {submitting ? "Отправка…" : "Отправить фото"}
      </button>
    </main>
  );
}
