import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { StepFeedbackForm } from "@/components/homework/StepFeedbackForm";

vi.mock("@/lib/api/homework-feedback", () => ({
  saveStepFeedback: vi.fn(),
  saveSubmissionFeedback: vi.fn(),
}));

vi.mock("@/lib/api/uploads", () => ({
  uploadAudio: vi.fn(),
  uploadImage: vi.fn(),
}));

vi.mock("@/components/homework/VoiceRecorder", () => ({
  VoiceRecorder: ({
    onRecorded,
  }: {
    onRecorded: (file: File, durationSec: number) => void;
  }) => (
    <button
      type="button"
      onClick={() =>
        onRecorded(new File(["audio"], "voice.webm", { type: "audio/webm" }), 5)
      }
    >
      mock-record
    </button>
  ),
}));

vi.mock("@/components/common/AuthenticatedImage", () => ({
  AuthenticatedImage: ({ alt }: { alt: string }) => <div>{alt}</div>,
}));

vi.mock("@/components/homework/AuthenticatedAudio", () => ({
  AuthenticatedAudio: () => <div>audio-player</div>,
}));

import { saveStepFeedback } from "@/lib/api/homework-feedback";

const mockedSave = vi.mocked(saveStepFeedback);

describe("StepFeedbackForm", () => {
  beforeEach(() => {
    mockedSave.mockReset();
  });

  it("saves text feedback for a step", async () => {
    mockedSave.mockResolvedValue({
      position: 0,
      title: "Self check",
      teacher_text: "Отлично",
      teacher_voice_url: null,
      teacher_image_urls: [],
      published_at: "2026-06-20T12:00:00Z",
    });

    render(
      <StepFeedbackForm
        homeworkId="hw-1"
        position={0}
        title="Разбор шага"
      />,
    );

    fireEvent.change(screen.getByPlaceholderText(/Что исправить/), {
      target: { value: "Отлично" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Сохранить разбор" }));

    await waitFor(() => {
      expect(mockedSave).toHaveBeenCalledWith("hw-1", 0, {
        teacher_text: "Отлично",
        teacher_voice_id: null,
        teacher_image_ids: [],
      });
    });

    expect(screen.getByText("Разбор сохранён")).toBeInTheDocument();
  });

  it("requires at least one feedback field", async () => {
    render(
      <StepFeedbackForm
        homeworkId="hw-1"
        position={0}
        title="Разбор шага"
      />,
    );

    expect(
      screen.getByRole("button", { name: "Сохранить разбор" }),
    ).toBeDisabled();
  });
});
