import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ChunkViewer } from "@/components/textbook/ChunkViewer";
import { getChunk } from "@/lib/api/textbook";

vi.mock("@/lib/api/textbook", () => ({
  getChunk: vi.fn(),
  fetchAudioBlob: vi.fn(),
}));

vi.mock("@/components/textbook/AudioPlayer", () => ({
  AudioPlayer: () => <div data-testid="audio-player" />,
}));

const mockedGetChunk = vi.mocked(getChunk);

const summaries = [
  { chunk_idx: 0, chunk_title: "Введение", has_audio: false },
  { chunk_idx: 1, chunk_title: "Свойства", has_audio: true },
];

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ChunkViewer", () => {
  it("renders lecture markdown from the API", async () => {
    mockedGetChunk.mockResolvedValue({
      topic: "Соли",
      chunk_idx: 0,
      chunk_title: "Введение",
      lecture: "# Соли\n\nОпределение соли.",
      has_audio: false,
    });

    render(
      <ChunkViewer topic="Соли" summaries={summaries} initialChunkIdx={0} />,
    );

    expect(await screen.findByRole("heading", { level: 1 })).toHaveTextContent(
      "Соли",
    );
    expect(screen.getByText("Определение соли.")).toBeInTheDocument();
  });

  it("loads another chunk when a sidebar item is clicked", async () => {
    mockedGetChunk
      .mockResolvedValueOnce({
        topic: "Соли",
        chunk_idx: 0,
        chunk_title: "Введение",
        lecture: "# Соли",
        has_audio: false,
      })
      .mockResolvedValueOnce({
        topic: "Соли",
        chunk_idx: 1,
        chunk_title: "Свойства",
        lecture: "# Свойства",
        has_audio: true,
      });

    render(
      <ChunkViewer topic="Соли" summaries={summaries} initialChunkIdx={0} />,
    );

    await screen.findByRole("heading", { level: 1, name: "Соли" });
    await userEvent.click(screen.getByRole("button", { name: /Свойства/i }));

    await waitFor(() => {
      expect(mockedGetChunk).toHaveBeenLastCalledWith("Соли", 1);
    });
    expect(await screen.findByRole("heading", { level: 1 })).toHaveTextContent(
      "Свойства",
    );
  });
});
