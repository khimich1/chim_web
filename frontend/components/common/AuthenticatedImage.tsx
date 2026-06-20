"use client";

import { useEffect, useState } from "react";

import { fetchAuthenticatedImageBlob } from "@/lib/api/authenticated-image";

export function AuthenticatedImage({
  src,
  alt,
  className,
}: {
  src: string;
  alt: string;
  className?: string;
}) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;

    async function load() {
      setFailed(false);
      setBlobUrl(null);

      try {
        const blob = await fetchAuthenticatedImageBlob(src);
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
        Не удалось загрузить изображение
      </p>
    );
  }

  if (!blobUrl) {
    return (
      <p className="text-sm text-zinc-400" aria-live="polite">
        Загрузка…
      </p>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={blobUrl} alt={alt} className={className} />
  );
}
