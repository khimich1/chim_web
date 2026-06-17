"use client";

import { useState } from "react";

import type { ChunkSummary } from "@/lib/api/types";

function ChunkNavList({
  summaries,
  activeChunkIdx,
  onSelect,
}: {
  summaries: ChunkSummary[];
  activeChunkIdx: number;
  onSelect: (chunkIdx: number) => void;
}) {
  return (
    <>
      {summaries.map((summary) => {
        const isActive = summary.chunk_idx === activeChunkIdx;
        return (
          <button
            key={summary.chunk_idx}
            type="button"
            onClick={() => onSelect(summary.chunk_idx)}
            aria-current={isActive ? "true" : undefined}
            className={`w-full rounded-md px-3 py-2.5 text-left text-sm transition min-h-[44px] ${
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
    </>
  );
}

export function ChunkNav({
  summaries,
  activeChunkIdx,
  onSelect,
}: {
  summaries: ChunkSummary[];
  activeChunkIdx: number;
  onSelect: (chunkIdx: number) => void;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const activeSummary = summaries.find((s) => s.chunk_idx === activeChunkIdx);

  const handleSelect = (chunkIdx: number) => {
    onSelect(chunkIdx);
    setMobileOpen(false);
  };

  return (
    <>
      {/* Desktop sidebar */}
      <nav
        aria-label="Чанки темы"
        className="hidden flex-col gap-1 lg:flex"
      >
        <ChunkNavList
          summaries={summaries}
          activeChunkIdx={activeChunkIdx}
          onSelect={handleSelect}
        />
      </nav>

      {/* Mobile collapsible panel */}
      <div className="lg:hidden">
        <button
          type="button"
          aria-expanded={mobileOpen}
          aria-controls="chunk-nav-mobile-panel"
          aria-label={`Текущий чанк: ${activeSummary?.chunk_title ?? "не выбран"}. Показать список чанков`}
          onClick={() => setMobileOpen((open) => !open)}
          className="chem-card flex w-full min-h-[44px] items-center justify-between gap-3 rounded-lg px-4 py-3 text-left text-sm font-medium text-zinc-800"
        >
          <span className="min-w-0 truncate">
            {activeSummary?.chunk_title ?? "Выберите чанк"}
          </span>
          <span
            aria-hidden
            className={`shrink-0 text-chem-teal transition-transform ${
              mobileOpen ? "rotate-180" : ""
            }`}
          >
            ▼
          </span>
        </button>

        {mobileOpen ? (
          <nav
            id="chunk-nav-mobile-panel"
            aria-label="Чанки темы"
            className="chem-card mt-2 flex max-h-64 flex-col gap-1 overflow-y-auto rounded-lg p-2"
          >
            <ChunkNavList
              summaries={summaries}
              activeChunkIdx={activeChunkIdx}
              onSelect={handleSelect}
            />
          </nav>
        ) : null}
      </div>
    </>
  );
}
