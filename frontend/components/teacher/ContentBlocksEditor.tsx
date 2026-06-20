"use client";

import { useEffect, useState } from "react";

import { ApiError, API_URL } from "@/lib/api/client";
import { uploadImage } from "@/lib/api/uploads";
import type { ContentBlock } from "@/lib/api/types";

function BlockImagePreview({ url }: { url: string }) {
  const path = url.startsWith("http") ? new URL(url).pathname : url;
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
        // preview optional
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
    return <p className="text-xs text-zinc-500">Загрузка превью…</p>;
  }

  return (
    <img
      src={src}
      alt="Загруженное изображение"
      className="mt-2 block h-auto max-w-full rounded-md border border-zinc-200 object-contain"
    />
  );
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
  const [uploadingIndex, setUploadingIndex] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  function updateBlock(index: number, block: ContentBlock) {
    onChange(blocks.map((item, i) => (i === index ? block : item)));
  }

  function removeBlock(index: number) {
    onChange(blocks.filter((_, i) => i !== index));
  }

  function addTextBlock() {
    onChange([...blocks, { type: "text", content: "" }]);
  }

  async function addImageBlock(file: File) {
    setError(null);
    const index = blocks.length;
    setUploadingIndex(index);
    try {
      const result = await uploadImage(file);
      onChange([...blocks, { type: "image", url: result.url }]);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Не удалось загрузить изображение.",
      );
    } finally {
      setUploadingIndex(null);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <span className="text-sm font-medium text-zinc-700">{label}</span>

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
                rows={3}
                className="chem-input w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm"
                placeholder="Текст задания…"
              />
            ) : block.url ? (
              <BlockImagePreview url={block.url} />
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
          {uploadingIndex !== null ? "Загрузка…" : "+ Изображение"}
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="sr-only"
            disabled={uploadingIndex !== null}
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

      {error ? (
        <p role="alert" className="text-sm text-[var(--chem-crimson)]">
          {error}
        </p>
      ) : null}
    </div>
  );
}
