"use client";

import { useEffect, useState } from "react";

import { fetchAudioBlob } from "@/lib/api/textbook";

export function AudioPlayer({
  topic,
  chunkIdx,
  hasAudio,
}: {
  topic: string;
  chunkIdx: number;
  hasAudio: boolean;
}) {
  const [src, setSrc] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hasAudio) {
      setSrc(null);
      setError(null);
      return;
    }

    let objectUrl: string | null = null;
    let cancelled = false;

    async function load() {
      try {
        const blob = await fetchAudioBlob(topic, chunkIdx);
        if (cancelled) {
          return;
        }
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
        setError(null);
      } catch {
        if (!cancelled) {
          setError("Не удалось загрузить аудио.");
          setSrc(null);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [topic, chunkIdx, hasAudio]);

  if (!hasAudio) {
    return null;
  }

  if (error) {
    return <p className="text-sm text-red-600">{error}</p>;
  }

  if (!src) {
    return <p className="text-sm text-zinc-500">Загрузка аудио…</p>;
  }

  return (
    <audio controls preload="none" src={src} className="w-full">
      Ваш браузер не поддерживает воспроизведение аудио.
    </audio>
  );
}
