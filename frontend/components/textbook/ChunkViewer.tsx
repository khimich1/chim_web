"use client";

import { useEffect, useState } from "react";

import { AudioPlayer } from "@/components/textbook/AudioPlayer";
import { ChunkNav } from "@/components/textbook/ChunkNav";
import { LectureContent } from "@/components/textbook/LectureContent";
import { getChunk } from "@/lib/api/textbook";
import { ApiError } from "@/lib/api/client";
import type { ChunkSummary, TextbookChunk } from "@/lib/api/types";

export function ChunkViewer({
  topic,
  summaries,
  initialChunkIdx = 0,
}: {
  topic: string;
  summaries: ChunkSummary[];
  initialChunkIdx?: number;
}) {
  const [chunkIdx, setChunkIdx] = useState(initialChunkIdx);
  const [chunk, setChunk] = useState<TextbookChunk | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getChunk(topic, chunkIdx);
        if (!cancelled) {
          setChunk(data);
        }
      } catch (err) {
        if (!cancelled) {
          setChunk(null);
          setError(
            err instanceof ApiError
              ? err.message
              : "Не удалось загрузить чанк.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [topic, chunkIdx]);

  const currentPosition = summaries.findIndex((item) => item.chunk_idx === chunkIdx);
  const prevSummary =
    currentPosition > 0 ? summaries[currentPosition - 1] : null;
  const nextSummary =
    currentPosition >= 0 && currentPosition < summaries.length - 1
      ? summaries[currentPosition + 1]
      : null;

  return (
    <div className="flex flex-col gap-4 lg:grid lg:grid-cols-[240px_minmax(0,1fr)] lg:gap-8">
      <ChunkNav
        summaries={summaries}
        activeChunkIdx={chunkIdx}
        onSelect={setChunkIdx}
      />

      <div className="min-w-0">
        {loading ? (
          <p className="text-sm text-zinc-500" aria-live="polite">
            Загрузка…
          </p>
        ) : error ? (
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
        ) : chunk ? (
          <article className="chem-card overflow-hidden rounded-xl pb-24 lg:pb-0">
            <header className="flex items-center gap-4 bg-chem-teal px-4 py-4 text-white sm:px-5">
              <span
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/20 text-sm font-bold"
                aria-label={`Чанк ${chunk.chunk_idx + 1}`}
              >
                {chunk.chunk_idx + 1}
              </span>
              <div className="min-w-0">
                <p className="text-xs font-medium uppercase tracking-wide text-white/75">
                  {topic}
                </p>
                <h2 className="truncate text-lg font-semibold">
                  {chunk.chunk_title}
                </h2>
              </div>
            </header>

            <div className="px-4 py-6 sm:px-5">
              {chunk.has_audio ? (
                <div className="mb-6 max-w-[70ch]">
                  <AudioPlayer
                    topic={topic}
                    chunkIdx={chunk.chunk_idx}
                    hasAudio={chunk.has_audio}
                  />
                </div>
              ) : null}

              <LectureContent lecture={chunk.lecture} />
            </div>
          </article>
        ) : null}

        <nav
          aria-label="Навигация по чанкам"
          className="fixed bottom-0 left-0 right-0 z-10 border-t border-zinc-200 bg-white/95 px-4 py-3 backdrop-blur-sm lg:static lg:mt-6 lg:border-t lg:border-zinc-200 lg:bg-transparent lg:px-0 lg:py-0 lg:pt-6 lg:backdrop-blur-none"
        >
          <div className="mx-auto flex max-w-5xl items-center justify-between gap-3">
            <button
              type="button"
              disabled={!prevSummary}
              onClick={() => prevSummary && setChunkIdx(prevSummary.chunk_idx)}
              className="min-h-[44px] min-w-[44px] rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 disabled:opacity-40"
            >
              Назад
            </button>
            <span className="text-sm text-zinc-500">
              {currentPosition >= 0
                ? `${currentPosition + 1} из ${summaries.length}`
                : null}
            </span>
            <button
              type="button"
              disabled={!nextSummary}
              onClick={() => nextSummary && setChunkIdx(nextSummary.chunk_idx)}
              className="min-h-[44px] min-w-[44px] rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 disabled:opacity-40"
            >
              Далее
            </button>
          </div>
        </nav>
      </div>
    </div>
  );
}
