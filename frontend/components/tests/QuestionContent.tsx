"use client";

import { useEffect, useState } from "react";

import { API_URL } from "@/lib/api/client";

// Backend substitutes `[рисунокNNNN]` with a bare image endpoint URL.
const IMAGE_URL_RE = /(\/api\/tests\/images\/[^\s)]+)/g;

/**
 * Loads a protected test image as a blob (the auth cookie is SameSite=lax and
 * is not sent for cross-site <img> subresources, so we fetch with credentials).
 */
function ApiImage({ path }: { path: string }) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;

    async function load() {
      try {
        const response = await fetch(`${API_URL}${path}`, {
          credentials: "include",
        });
        if (!response.ok || cancelled) {
          return;
        }
        const blob = await response.blob();
        objectUrl = URL.createObjectURL(blob);
        if (!cancelled) {
          setSrc(objectUrl);
        }
      } catch {
        // Leave image unrendered on failure; question text still shows.
      }
    }

    void load();

    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [path]);

  if (!src) {
    return null;
  }

  return (
    <img
      src={src}
      alt="Иллюстрация к заданию"
      className="my-3 max-w-full rounded-md border border-zinc-200"
    />
  );
}

export function QuestionContent({ text }: { text: string }) {
  const parts = text.split(IMAGE_URL_RE);

  return (
    <div className="text-zinc-900">
      {parts.map((part, index) =>
        /^\/api\/tests\/images\//.test(part) ? (
          <ApiImage key={index} path={part} />
        ) : (
          <span key={index} className="whitespace-pre-wrap leading-7">
            {part}
          </span>
        ),
      )}
    </div>
  );
}
