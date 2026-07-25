import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { VoiceRecorder } from "@/components/homework/VoiceRecorder";

function mockMediaRecorder() {
  const stopTrack = vi.fn();
  const stream = {
    getTracks: () => [{ stop: stopTrack }],
  } as unknown as MediaStream;

  class FakeMediaRecorder {
    state = "inactive";
    ondataavailable: ((event: { data: Blob }) => void) | null = null;
    onstop: (() => void) | null = null;

    constructor() {}

    start() {
      this.state = "recording";
    }

    stop() {
      this.state = "inactive";
      this.ondataavailable?.({
        data: new Blob(["audio"], { type: "audio/webm" }),
      });
      this.onstop?.();
    }
  }

  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: {
      getUserMedia: vi.fn().mockResolvedValue(stream),
    },
  });

  vi.stubGlobal("MediaRecorder", FakeMediaRecorder);
  (
    FakeMediaRecorder as unknown as { isTypeSupported: (type: string) => boolean }
  ).isTypeSupported = () => true;

  Object.defineProperty(URL, "createObjectURL", {
    configurable: true,
    writable: true,
    value: vi.fn(() => "blob:mock-audio"),
  });
  Object.defineProperty(URL, "revokeObjectURL", {
    configurable: true,
    writable: true,
    value: vi.fn(),
  });

  return { stopTrack };
}

describe("VoiceRecorder", () => {
  beforeEach(() => {
    mockMediaRecorder();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders visible «Записать голос» button by default", () => {
    render(<VoiceRecorder onRecorded={vi.fn()} />);

    expect(
      screen.getByRole("button", { name: "Записать голос" }),
    ).toBeInTheDocument();
  });

  it("icon variant has no visible «Записать голос» label and starts recording", async () => {
    render(<VoiceRecorder variant="icon" onRecorded={vi.fn()} />);

    expect(screen.queryByText("Записать голос")).not.toBeInTheDocument();

    const mic = screen.getByRole("button", { name: "Записать голос" });
    fireEvent.click(mic);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Остановить" }),
      ).toBeInTheDocument();
    });
  });

  it("icon variant supports preview confirm and discard", async () => {
    const onRecorded = vi.fn();
    render(<VoiceRecorder variant="icon" onRecorded={onRecorded} />);

    fireEvent.click(screen.getByRole("button", { name: "Записать голос" }));

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Остановить" }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Остановить" }));

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Использовать запись" }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Перезаписать" }));

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Записать голос" }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Записать голос" }));
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Остановить" }),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: "Остановить" }));
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Использовать запись" }),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: "Использовать запись" }));

    expect(onRecorded).toHaveBeenCalledTimes(1);
    expect(onRecorded.mock.calls[0][0]).toBeInstanceOf(File);
  });
});
