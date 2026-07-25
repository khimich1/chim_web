"use client";

import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";
import { Formula } from "@/components/textbook/Formula";
import type { ContentBlock } from "@/lib/api/types";
import { splitTextWithFormulas } from "@/lib/tests/question-text";

export type QuestionImageItem = { src: string; alt: string };

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

function collectImageItems(blocks: ContentBlock[]): QuestionImageItem[] {
  const items: QuestionImageItem[] = [];
  for (const block of blocks) {
    if (block.type === "image" && block.url) {
      items.push({ src: block.url, alt: "Иллюстрация к заданию" });
    }
  }
  return items;
}

export function CustomQuestionContent({
  blocks,
  onImageClick,
}: {
  blocks: ContentBlock[];
  onImageClick?: (items: QuestionImageItem[], index: number) => void;
}) {
  if (!blocks.length) {
    return <p className="text-sm text-zinc-500">Текст задания отсутствует.</p>;
  }

  const imageItems = collectImageItems(blocks);
  let imageOrdinal = 0;

  return (
    <div className="max-w-full overflow-x-hidden">
      {blocks.map((block, index) => {
        if (block.type === "text" && block.content) {
          return <TextBlock key={index} text={block.content} />;
        }
        if (block.type === "image" && block.url) {
          const imageIndex = imageOrdinal;
          imageOrdinal += 1;
          const image = (
            <AuthenticatedImage
              src={block.url}
              alt="Иллюстрация к заданию"
              className="my-3 block h-auto max-w-full rounded-md border border-zinc-200 object-contain"
            />
          );

          if (!onImageClick) {
            return <div key={index}>{image}</div>;
          }

          return (
            <button
              key={index}
              type="button"
              onClick={() => onImageClick(imageItems, imageIndex)}
              className="block w-full cursor-zoom-in rounded-md text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-400"
              aria-label={`Открыть иллюстрацию ${imageIndex + 1}`}
            >
              {image}
            </button>
          );
        }
        return null;
      })}
    </div>
  );
}
