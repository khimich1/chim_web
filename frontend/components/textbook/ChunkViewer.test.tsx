import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ChunkViewer } from "@/components/textbook/ChunkViewer";
import { getChunk } from "@/lib/api/textbook";
import { warmupNeuroQuiz } from "@/lib/api/neuroquiz";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock("@/lib/api/textbook", () => ({
  getChunk: vi.fn(),
  fetchAudioBlob: vi.fn(),
}));

vi.mock("@/lib/api/neuroquiz", () => ({
  warmupNeuroQuiz: vi.fn().mockResolvedValue(undefined),
  getNeuroQuizSession: vi.fn(),
  answerNeuroQuiz: vi.fn(),
  skipNeuroQuiz: vi.fn(),
  voteNeuroQuiz: vi.fn(),
}));

vi.mock("@/components/textbook/AudioPlayer", () => ({
  AudioPlayer: () => <div data-testid="audio-player" />,
}));

vi.mock("@/components/textbook/VideoEmbed", () => ({
  VideoEmbed: ({ videoUrl }: { videoUrl: string }) => (
    <div data-testid="video-embed">{videoUrl}</div>
  ),
}));

vi.mock("@/components/textbook/NeuroQuizOverlay", () => ({
  NeuroQuizOverlay: ({
    open,
    onSkip,
    onComplete,
  }: {
    open: boolean;
    onSkip: () => void;
    onComplete: () => void;
  }) =>
    open ? (
      <div role="dialog" data-testid="neuroquiz-overlay">
        <button type="button" onClick={onSkip}>
          mock-skip
        </button>
        <button type="button" onClick={onComplete}>
          mock-complete
        </button>
      </div>
    ) : null,
}));

const mockedGetChunk = vi.mocked(getChunk);
const mockedWarmup = vi.mocked(warmupNeuroQuiz);

const summaries = [
  { chunk_idx: 0, chunk_title: "Введение", has_audio: false },
  { chunk_idx: 1, chunk_title: "Свойства", has_audio: true },
];

beforeEach(() => {
  vi.clearAllMocks();
  pushMock.mockReset();
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

  it("renders video embed only on the first chunk", async () => {
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
      <ChunkViewer
        topic="Соли"
        summaries={summaries}
        initialChunkIdx={0}
        videoUrl="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
      />,
    );

    expect(await screen.findByTestId("video-embed")).toHaveTextContent(
      "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    );

    const navButtons = screen.getAllByRole("button", { name: /Свойства/i });
    const sidebarButton = navButtons.find(
      (button) => button.getAttribute("aria-current") !== "true",
    );
    await userEvent.click(sidebarButton!);

    await screen.findByRole("heading", { level: 2, name: "Свойства" });
    expect(screen.queryByTestId("video-embed")).not.toBeInTheDocument();
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

  it("opens neuroquiz on Далее when enabled and warms up on load", async () => {
    mockedGetChunk.mockResolvedValue({
      topic: "Соли",
      chunk_idx: 0,
      chunk_title: "Введение",
      lecture: "# Соли",
      has_audio: false,
    });

    render(
      <ChunkViewer
        topic="Соли"
        summaries={summaries}
        initialChunkIdx={0}
        neuroquizEnabled
        catalogHref="/student/textbook?section=basics"
      />,
    );

    await screen.findByRole("heading", { level: 2, name: "Введение" });
    expect(mockedWarmup).toHaveBeenCalledWith("Соли", 0);

    await userEvent.click(screen.getByRole("button", { name: "Далее" }));
    expect(screen.getByTestId("neuroquiz-overlay")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "mock-skip" }));
    expect(screen.queryByTestId("neuroquiz-overlay")).not.toBeInTheDocument();
    expect(mockedGetChunk).toHaveBeenLastCalledWith("Соли", 0);
  });

  it("navigates to catalog after complete on last chunk", async () => {
    mockedGetChunk.mockResolvedValue({
      topic: "Соли",
      chunk_idx: 1,
      chunk_title: "Свойства",
      lecture: "# Свойства",
      has_audio: true,
    });

    render(
      <ChunkViewer
        topic="Соли"
        summaries={summaries}
        initialChunkIdx={1}
        neuroquizEnabled
        catalogHref="/student/textbook?section=basics"
      />,
    );

    await screen.findByRole("heading", { level: 2, name: "Свойства" });
    const next = screen.getByRole("button", { name: "Далее" });
    expect(next).not.toBeDisabled();
    await userEvent.click(next);
    await userEvent.click(screen.getByRole("button", { name: "mock-complete" }));
    expect(pushMock).toHaveBeenCalledWith("/student/textbook?section=basics");
  });

  it("keeps old Далее behavior when neuroquiz is disabled", async () => {
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
    expect(mockedWarmup).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: "Далее" }));
    await waitFor(() => {
      expect(mockedGetChunk).toHaveBeenLastCalledWith("Соли", 1);
    });
    expect(screen.queryByTestId("neuroquiz-overlay")).not.toBeInTheDocument();
  });

  it("does not open neuroquiz from sidebar or Назад when enabled", async () => {
    mockedGetChunk
      .mockResolvedValueOnce({
        topic: "Соли",
        chunk_idx: 1,
        chunk_title: "Свойства",
        lecture: "# Свойства",
        has_audio: true,
      })
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
      <ChunkViewer
        topic="Соли"
        summaries={summaries}
        initialChunkIdx={1}
        neuroquizEnabled
      />,
    );

    await screen.findByRole("heading", { level: 2, name: "Свойства" });
    expect(screen.queryByTestId("neuroquiz-overlay")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Назад" }));
    await screen.findByRole("heading", { level: 2, name: "Введение" });
    expect(screen.queryByTestId("neuroquiz-overlay")).not.toBeInTheDocument();

    const navButtons = screen.getAllByRole("button", { name: /Свойства/i });
    const sidebarButton = navButtons.find(
      (button) => button.getAttribute("aria-current") !== "true",
    );
    expect(sidebarButton).toBeTruthy();
    await userEvent.click(sidebarButton!);
    await screen.findByRole("heading", { level: 2, name: "Свойства" });
    expect(screen.queryByTestId("neuroquiz-overlay")).not.toBeInTheDocument();
  });

  it("navigates to next chunk after complete on a non-last chunk", async () => {
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
      <ChunkViewer
        topic="Соли"
        summaries={summaries}
        initialChunkIdx={0}
        neuroquizEnabled
        catalogHref="/student/textbook?section=basics"
      />,
    );

    await screen.findByRole("heading", { level: 2, name: "Введение" });
    await userEvent.click(screen.getByRole("button", { name: "Далее" }));
    expect(screen.getByTestId("neuroquiz-overlay")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "mock-complete" }));

    await screen.findByRole("heading", { level: 2, name: "Свойства" });
    expect(pushMock).not.toHaveBeenCalled();
    expect(mockedGetChunk).toHaveBeenLastCalledWith("Соли", 1);
    expect(screen.queryByTestId("neuroquiz-overlay")).not.toBeInTheDocument();
  });
});
