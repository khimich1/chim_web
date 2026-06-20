"use client";

import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";
import { Formula } from "@/components/textbook/Formula";
import type { ContentBlock } from "@/lib/api/types";
import { splitTextWithFormulas } from "@/lib/tests/question-text";

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
          return (
            <AuthenticatedImage
              key={index}
              src={block.url}
              alt="Иллюстрация к заданию"
              className="my-3 block h-auto max-w-full rounded-md border border-zinc-200 object-contain"
            />
          );
        }
        return null;
      })}
    </div>
  );
}
