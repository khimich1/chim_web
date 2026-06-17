"use client";

import { useEffect, useState } from "react";

import { Formula } from "@/components/textbook/Formula";
import { API_URL } from "@/lib/api/client";
import { splitTextWithFormulas } from "@/lib/tests/question-text";

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
      className="my-3 block h-auto max-w-full rounded-md border border-zinc-200 object-contain"
    />
  );
}

function TextWithFormulas({ text }: { text: string }) {
  const segments = splitTextWithFormulas(text);

  return (
    <>
      {segments.map((segment, index) =>
        segment.kind === "formula" ? (
          <Formula key={index}>{segment.value}</Formula>
        ) : (
          <span key={index} className="whitespace-pre-wrap">
            {segment.value}
          </span>
        ),
      )}
    </>
  );
}

export function QuestionContent({ text }: { text: string }) {
  const parts = text.split(IMAGE_URL_RE);

  return (
    <div className="max-w-full overflow-x-hidden text-[1.0625rem] leading-7 text-zinc-900">
      {parts.map((part, index) =>
        /^\/api\/tests\/images\//.test(part) ? (
          <ApiImage key={index} path={part} />
        ) : (
          <TextWithFormulas key={index} text={part} />
        ),
      )}
    </div>
  );
}
