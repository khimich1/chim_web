"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import { AudioPlayer } from "@/components/textbook/AudioPlayer";
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

  const currentSummary = summaries.find((item) => item.chunk_idx === chunkIdx);
  const currentPosition = summaries.findIndex((item) => item.chunk_idx === chunkIdx);
  const prevSummary =
    currentPosition > 0 ? summaries[currentPosition - 1] : null;
  const nextSummary =
    currentPosition >= 0 && currentPosition < summaries.length - 1
      ? summaries[currentPosition + 1]
      : null;

  return (
    <div className="grid gap-8 lg:grid-cols-[240px_1fr]">
      <nav aria-label="Чанки темы" className="flex flex-col gap-1">
        {summaries.map((summary) => {
          const isActive = summary.chunk_idx === chunkIdx;
          return (
            <button
              key={summary.chunk_idx}
              type="button"
              onClick={() => setChunkIdx(summary.chunk_idx)}
              className={`rounded-md px-3 py-2 text-left text-sm transition ${
                isActive
                  ? "chem-nav-active"
                  : "text-zinc-700 hover:bg-chem-peach/25"
              }`}
            >
              <span className="block font-medium">{summary.chunk_title}</span>
              <span
                className={`mt-0.5 block text-xs ${
                  isActive ? "text-white/75" : "text-zinc-500"
                }`}
              >
                Чанк {summary.chunk_idx + 1}
                {summary.has_audio ? " · аудио" : ""}
              </span>
            </button>
          );
        })}
      </nav>

      <article className="min-w-0">
        {loading ? (
          <p className="text-sm text-zinc-500">Загрузка…</p>
        ) : error ? (
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
        ) : chunk ? (
          <>
            <header className="mb-6">
              <p className="chem-kicker text-sm normal-case tracking-normal">{topic}</p>
              <h2 className="mt-1 text-2xl font-semibold text-zinc-900">
                {chunk.chunk_title}
              </h2>
            </header>

            {chunk.has_audio ? (
              <div className="mb-6">
                <AudioPlayer
                  topic={topic}
                  chunkIdx={chunk.chunk_idx}
                  hasAudio={chunk.has_audio}
                />
              </div>
            ) : null}

            <div className="space-y-3 leading-7 text-zinc-800 [&_h1]:text-2xl [&_h1]:font-bold [&_h2]:text-xl [&_h2]:font-semibold [&_h3]:text-lg [&_h3]:font-semibold [&_ol]:list-decimal [&_ol]:pl-6 [&_p]:mb-3 [&_ul]:list-disc [&_ul]:pl-6">
              <ReactMarkdown>{chunk.lecture}</ReactMarkdown>
            </div>
          </>
        ) : null}

        <div className="mt-8 flex items-center justify-between gap-4 border-t border-zinc-200 pt-6">
          <button
            type="button"
            disabled={!prevSummary}
            onClick={() => prevSummary && setChunkIdx(prevSummary.chunk_idx)}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 disabled:opacity-40"
          >
            Назад
          </button>
          <span className="text-sm text-zinc-500">
            {currentSummary
              ? `${currentPosition + 1} из ${summaries.length}`
              : null}
          </span>
          <button
            type="button"
            disabled={!nextSummary}
            onClick={() => nextSummary && setChunkIdx(nextSummary.chunk_idx)}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 disabled:opacity-40"
          >
            Далее
          </button>
        </div>
      </article>
    </div>
  );
}
