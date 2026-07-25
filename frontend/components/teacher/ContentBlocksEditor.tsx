"use client";

import { useRef, useState } from "react";

import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";
import {
  ImageLightbox,
  type LightboxItem,
} from "@/components/common/ImageLightbox";
import { ApiError } from "@/lib/api/client";
import { uploadImage } from "@/lib/api/uploads";
import type { ContentBlock } from "@/lib/api/types";
import {
  CONTENT_IMAGE_CLASS,
  IMAGE_INTAKE_HINT,
  imageFilesFromDataTransfer,
} from "@/lib/image-intake";

const EDITOR_INTAKE_LIMIT = 10;

function collectEditorImageItems(blocks: ContentBlock[]): LightboxItem[] {
  const items: LightboxItem[] = [];
  for (const block of blocks) {
    if (block.type === "image" && block.url) {
      items.push({ src: block.url, alt: "Загруженное изображение" });
    }
  }
  return items;
}

export function ContentBlocksEditor({
  blocks,
  onChange,
  label,
}: {
  blocks: ContentBlock[];
  onChange: (blocks: ContentBlock[]) => void;
  label: string;
}) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [activeBlockIndex, setActiveBlockIndex] = useState<number | null>(null);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxItems, setLightboxItems] = useState<LightboxItem[]>([]);
  const [lightboxIndex, setLightboxIndex] = useState(0);
  const blocksRef = useRef(blocks);
  blocksRef.current = blocks;

  const imageItems = collectEditorImageItems(blocks);

  function openLightbox(items: LightboxItem[], index: number) {
    if (items.length === 0) {
      return;
    }
    setLightboxItems(items);
    setLightboxIndex(index);
    setLightboxOpen(true);
  }

  function updateBlock(index: number, block: ContentBlock) {
    onChange(blocks.map((item, i) => (i === index ? block : item)));
  }

  function removeBlock(index: number) {
    onChange(blocks.filter((_, i) => i !== index));
  }

  function addTextBlock() {
    onChange([...blocks, { type: "text", content: "" }]);
  }

  function insertImageBlocks(urls: string[]) {
    if (urls.length === 0) {
      return;
    }
    const current = blocksRef.current;
    const imageBlocks: ContentBlock[] = urls.map((url) => ({
      type: "image",
      url,
    }));
    const insertAt =
      activeBlockIndex !== null && activeBlockIndex >= 0
        ? activeBlockIndex + 1
        : current.length;
    const next = [
      ...current.slice(0, insertAt),
      ...imageBlocks,
      ...current.slice(insertAt),
    ];
    onChange(next);
    blocksRef.current = next;
  }

  async function uploadFiles(files: File[], truncated: boolean) {
    if (uploading || files.length === 0) {
      return;
    }
    setError(null);
    setNotice(
      truncated
        ? "За раз можно загрузить не более 10 изображений; лишние отброшены."
        : null,
    );
    setUploading(true);
    const urls: string[] = [];
    try {
      for (const file of files) {
        const result = await uploadImage(file);
        urls.push(result.url);
      }
      insertImageBlocks(urls);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось загрузить изображение.",
      );
      if (urls.length > 0) {
        insertImageBlocks(urls);
      }
    } finally {
      setUploading(false);
    }
  }

  async function addImageBlock(file: File) {
    await uploadFiles([file], false);
  }

  function handlePaste(event: React.ClipboardEvent) {
    if (uploading) {
      return;
    }
    const { files, truncated } = imageFilesFromDataTransfer(
      event.clipboardData,
      { limit: EDITOR_INTAKE_LIMIT },
    );
    if (files.length === 0) {
      return;
    }
    event.preventDefault();
    void uploadFiles(files, truncated);
  }

  function handleDragOver(event: React.DragEvent) {
    if (uploading) {
      return;
    }
    const { files } = imageFilesFromDataTransfer(event.dataTransfer, {
      limit: EDITOR_INTAKE_LIMIT,
    });
    if (files.length === 0) {
      return;
    }
    event.preventDefault();
  }

  function handleDrop(event: React.DragEvent) {
    if (uploading) {
      return;
    }
    const { files, truncated } = imageFilesFromDataTransfer(event.dataTransfer, {
      limit: EDITOR_INTAKE_LIMIT,
    });
    if (files.length === 0) {
      return;
    }
    event.preventDefault();
    void uploadFiles(files, truncated);
  }

  return (
    <div
      className="flex flex-col gap-3"
      data-testid="content-blocks-intake"
      onPaste={handlePaste}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <span className="text-sm font-medium text-zinc-700">{label}</span>
      <p className="text-xs text-zinc-500">{IMAGE_INTAKE_HINT}</p>

      {blocks.length === 0 ? (
        <p className="text-sm text-zinc-500">Добавьте хотя бы один блок.</p>
      ) : null}

      <ul className="flex flex-col gap-3">
        {blocks.map((block, index) => (
          <li
            key={`${block.type}-${index}`}
            className="rounded-lg border border-zinc-200 bg-zinc-50 p-3"
          >
            <div className="mb-2 flex items-center justify-between gap-2">
              <span className="text-xs font-medium uppercase text-zinc-500">
                {block.type === "text" ? "Текст" : "Изображение"}
              </span>
              <button
                type="button"
                onClick={() => removeBlock(index)}
                className="text-xs text-[var(--chem-crimson)] hover:underline"
              >
                Удалить
              </button>
            </div>

            {block.type === "text" ? (
              <textarea
                value={block.content ?? ""}
                onChange={(e) =>
                  updateBlock(index, { type: "text", content: e.target.value })
                }
                onFocus={() => setActiveBlockIndex(index)}
                rows={3}
                className="chem-input w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm"
                placeholder="Текст задания…"
              />
            ) : block.url ? (
              <button
                type="button"
                onClick={() => {
                  const imageIndex = blocks
                    .slice(0, index)
                    .filter((b) => b.type === "image" && b.url).length;
                  openLightbox(imageItems, imageIndex);
                }}
                className="block w-full cursor-zoom-in text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-400"
                aria-label={`Открыть изображение ${
                  blocks
                    .slice(0, index)
                    .filter((b) => b.type === "image" && b.url).length + 1
                }`}
              >
                <AuthenticatedImage
                  src={block.url}
                  alt="Загруженное изображение"
                  className={CONTENT_IMAGE_CLASS}
                />
              </button>
            ) : null}
          </li>
        ))}
      </ul>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={addTextBlock}
          className="rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-700 hover:border-zinc-400"
        >
          + Текст
        </button>
        <label className="cursor-pointer rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-700 hover:border-zinc-400">
          {uploading ? "Загрузка…" : "+ Изображение"}
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="sr-only"
            disabled={uploading}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) {
                void addImageBlock(file);
              }
              e.target.value = "";
            }}
          />
        </label>
      </div>

      {notice ? (
        <p role="status" className="text-sm text-zinc-600">
          {notice}
        </p>
      ) : null}

      {error ? (
        <p role="alert" className="text-sm text-[var(--chem-crimson)]">
          {error}
        </p>
      ) : null}

      <ImageLightbox
        open={lightboxOpen}
        items={lightboxItems}
        index={lightboxIndex}
        onClose={() => setLightboxOpen(false)}
        onIndexChange={setLightboxIndex}
      />
    </div>
  );
}
