import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
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

  it("renders callout boxes and formula chips from markdown", async () => {
    mockedGetChunk.mockResolvedValue({
      topic: "Соли",
      chunk_idx: 0,
      chunk_title: "Введение",
      lecture: [
        "## Раздел",
        "",
        "📌 Соль — ионное соединение.",
        "💡 Формула `NaCl` — пример соли.",
      ].join("\n"),
      has_audio: false,
    });

    render(
      <ChunkViewer topic="Соли" summaries={summaries} initialChunkIdx={0} />,
    );

    await screen.findByRole("note", { name: "Важно" });
    expect(screen.getByRole("note", { name: "Пример" })).toBeInTheDocument();
    expect(screen.getByText("Соль — ионное соединение.")).toBeInTheDocument();

    const formula = screen.getByText("NaCl");
    expect(formula.tagName).toBe("CODE");
    expect(formula).toHaveClass("chem-formula");
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

    await screen.findByRole("heading", { level: 2, name: "Введение" });
    const navButtons = screen.getAllByRole("button", { name: /Свойства/i });
    const sidebarButton = navButtons.find(
      (button) => button.getAttribute("aria-current") !== "true",
    );
    expect(sidebarButton).toBeTruthy();
    await userEvent.click(sidebarButton!);

    await waitFor(() => {
      expect(mockedGetChunk).toHaveBeenLastCalledWith("Соли", 1);
    });
    expect(
      await screen.findByRole("heading", { level: 2, name: "Свойства" }),
    ).toBeInTheDocument();
  });

  it("toggles mobile chunk nav panel open and closed", async () => {
    mockedGetChunk.mockResolvedValue({
      topic: "Соли",
      chunk_idx: 0,
      chunk_title: "Введение",
      lecture: "# Соли",
      has_audio: false,
    });

    render(
      <ChunkViewer topic="Соли" summaries={summaries} initialChunkIdx={0} />,
    );

    await screen.findByRole("heading", { level: 2, name: "Введение" });

    const toggle = screen.getByRole("button", {
      name: /Показать список чанков/i,
    });
    expect(toggle).toHaveAttribute("aria-expanded", "false");

    await userEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");

    const panel = document.getElementById("chunk-nav-mobile-panel");
    expect(panel).toBeInTheDocument();
    expect(
      within(panel!).getByRole("button", { name: /Свойства/i }),
    ).toBeInTheDocument();

    await userEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(document.getElementById("chunk-nav-mobile-panel")).toBeNull();
  });
});
