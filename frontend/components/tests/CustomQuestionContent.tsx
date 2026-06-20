"use client";

import { useEffect, useState } from "react";

import { Formula } from "@/components/textbook/Formula";
import { API_URL } from "@/lib/api/client";
import type { ContentBlock } from "@/lib/api/types";
import { splitTextWithFormulas } from "@/lib/tests/question-text";

function UploadImage({ path }: { path: string }) {
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
        // image optional
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

function TextBlock({ text }: { text: string }) {
  const segments = splitTextWithFormulas(text);

  return (
    <p className="whitespace-pre-wrap text-[1.0625rem] leading-7 text-zinc-900">
      {segments.map((segment, index) =>
        segment.kind === "formula" ? (
          <Formula key={index}>{segment.value}</Formula>
        ) : (
          <span key={index}>{segment.value}</span>
        ),
      )}
    </p>
  );
}

export function CustomQuestionContent({
  blocks,
}: {
  blocks: ContentBlock[];
}) {
  if (!blocks.length) {
    return <p className="text-sm text-zinc-500">Текст задания отсутствует.</p>;
  }

  return (
    <div className="max-w-full overflow-x-hidden">
      {blocks.map((block, index) => {
        if (block.type === "text" && block.content) {
          return <TextBlock key={index} text={block.content} />;
        }
        if (block.type === "image" && block.url) {
          const path = block.url.startsWith("http")
            ? new URL(block.url).pathname
            : block.url;
          return <UploadImage key={index} path={path} />;
        }
        return null;
      })}
    </div>
  );
}
