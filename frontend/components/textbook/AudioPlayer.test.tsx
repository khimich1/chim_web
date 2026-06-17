import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AudioPlayer, formatAudioTime } from "@/components/textbook/AudioPlayer";
import { fetchAudioBlob } from "@/lib/api/textbook";

vi.mock("@/lib/api/textbook", () => ({
  fetchAudioBlob: vi.fn(),
}));

const mockedFetchAudioBlob = vi.mocked(fetchAudioBlob);

describe("formatAudioTime", () => {
  it("formats seconds as m:ss", () => {
    expect(formatAudioTime(0)).toBe("0:00");
    expect(formatAudioTime(5)).toBe("0:05");
    expect(formatAudioTime(65)).toBe("1:05");
    expect(formatAudioTime(600)).toBe("10:00");
  });

  it("handles invalid values", () => {
    expect(formatAudioTime(Number.NaN)).toBe("0:00");
    expect(formatAudioTime(-3)).toBe("0:00");
  });
});

describe("AudioPlayer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(globalThis.URL, "createObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(() => "blob:audio-test"),
    });
    Object.defineProperty(globalThis.URL, "revokeObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(),
    });
    vi.spyOn(HTMLMediaElement.prototype, "play").mockImplementation(() =>
      Promise.resolve(),
    );
    vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => {});
  });

  it("shows loading state while audio blob is fetched", () => {
    mockedFetchAudioBlob.mockReturnValue(new Promise(() => {}));

    render(<AudioPlayer topic="Соли" chunkIdx={1} hasAudio />);

    expect(screen.getByText("Загрузка аудио…")).toBeInTheDocument();
  });

  it("shows error when audio blob fails to load", async () => {
    mockedFetchAudioBlob.mockRejectedValue(new Error("network"));

    render(<AudioPlayer topic="Соли" chunkIdx={1} hasAudio />);

    expect(
      await screen.findByText("Не удалось загрузить аудио."),
    ).toBeInTheDocument();
  });

  it("renders nothing when chunk has no audio", () => {
    const { container } = render(
      <AudioPlayer topic="Соли" chunkIdx={0} hasAudio={false} />,
    );

    expect(container).toBeEmptyDOMElement();
    expect(mockedFetchAudioBlob).not.toHaveBeenCalled();
  });

  it("toggles play and pause with accessible labels", async () => {
    mockedFetchAudioBlob.mockResolvedValue(new Blob(["audio"], { type: "audio/ogg" }));

    render(<AudioPlayer topic="Соли" chunkIdx={1} hasAudio />);

    const playButton = await screen.findByRole("button", {
      name: "Воспроизведение",
    });
    const audio = document.querySelector("audio");
    expect(audio).toHaveAttribute("src", "blob:audio-test");

    await userEvent.click(playButton);
    fireEvent.play(audio!);

    expect(
      await screen.findByRole("button", { name: "Пауза" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Воспроизведение")).toHaveClass("sr-only");

    await userEvent.click(screen.getByRole("button", { name: "Пауза" }));
    fireEvent.pause(audio!);

    expect(
      await screen.findByRole("button", { name: "Воспроизведение" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Пауза")).toHaveClass("sr-only");
  });

  it("exposes ARIA for progress and volume controls", async () => {
    mockedFetchAudioBlob.mockResolvedValue(new Blob(["audio"], { type: "audio/ogg" }));

    render(<AudioPlayer topic="Соли" chunkIdx={1} hasAudio />);

    expect(
      await screen.findByRole("group", { name: "Аудиоплеер" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("slider", { name: "Прогресс воспроизведения" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("slider", { name: "Громкость" })).toBeInTheDocument();
    expect(screen.getByText("0:00 / 0:00")).toBeInTheDocument();
  });

  it("seeks with arrow keys on the player container", async () => {
    mockedFetchAudioBlob.mockResolvedValue(new Blob(["audio"], { type: "audio/ogg" }));

    render(<AudioPlayer topic="Соли" chunkIdx={1} hasAudio />);

    const player = await screen.findByRole("group", { name: "Аудиоплеер" });

    const audio = await waitFor(() => {
      const element = document.querySelector("audio") as HTMLAudioElement | null;
      if (!element) {
        throw new Error("audio element not mounted");
      }
      return element;
    });

    await waitFor(async () => {
      await act(async () => {
        Object.defineProperty(audio, "duration", {
          configurable: true,
          value: 120,
        });
        audio.currentTime = 30;
        fireEvent.loadedMetadata(audio);
        fireEvent.timeUpdate(audio);
      });
      expect(screen.getByText("0:30 / 2:00")).toBeInTheDocument();
    });

    fireEvent.keyDown(player, { key: "ArrowRight" });
    expect(audio.currentTime).toBe(35);

    fireEvent.keyDown(player, { key: "ArrowLeft" });
    expect(audio.currentTime).toBe(30);
  });
});
