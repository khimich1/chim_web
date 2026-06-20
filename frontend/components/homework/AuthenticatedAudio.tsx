"use client";

import { useEffect, useRef, useState } from "react";

import { fetchAuthenticatedAudioBlob } from "@/lib/api/authenticated-audio";

export function AuthenticatedAudio({
  src,
  className,
}: {
  src: string;
  className?: string;
}) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;

    async function load() {
      setFailed(false);
      setBlobUrl(null);

      try {
        const blob = await fetchAuthenticatedAudioBlob(src);
        if (cancelled) {
          return;
        }
        objectUrl = URL.createObjectURL(blob);
        setBlobUrl(objectUrl);
      } catch {
        if (!cancelled) {
          setFailed(true);
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
  }, [src]);

  if (failed) {
    return (
      <p className="text-sm text-zinc-500" role="status">
        Не удалось загрузить аудио
      </p>
    );
  }

  if (!blobUrl) {
    return (
      <p className="text-sm text-zinc-400" aria-live="polite">
        Загрузка аудио…
      </p>
    );
  }

  return (
    <audio ref={audioRef} src={blobUrl} controls className={className}>
      <track kind="captions" />
    </audio>
  );
}
