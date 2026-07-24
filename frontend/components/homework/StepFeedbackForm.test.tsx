import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { StepFeedbackForm } from "@/components/homework/StepFeedbackForm";
import { uploadImage } from "@/lib/api/uploads";
import { IMAGE_INTAKE_HINT } from "@/lib/image-intake";

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
  AuthenticatedImage: ({
    alt,
    className,
  }: {
    alt: string;
    className?: string;
  }) => (
    <div data-testid="feedback-preview" className={className}>
      {alt}
    </div>
  ),
}));

vi.mock("@/components/homework/AuthenticatedAudio", () => ({
  AuthenticatedAudio: () => <div>audio-player</div>,
}));

import { saveStepFeedback } from "@/lib/api/homework-feedback";

const mockedSave = vi.mocked(saveStepFeedback);
const mockedUpload = vi.mocked(uploadImage);

function clipboardDataFor(files: File[]) {
  const items = files.map((file) => ({
    kind: "file" as const,
    type: file.type,
    getAsFile: () => file,
  }));
  return {
    items: {
      length: items.length,
      ...items,
      [Symbol.iterator]: function* () {
        yield* items;
      },
    },
    files: {
      length: files.length,
      ...files,
      item: (index: number) => files[index] ?? null,
      [Symbol.iterator]: function* () {
        yield* files;
      },
    },
  };
}

describe("StepFeedbackForm", () => {
  beforeEach(() => {
    mockedSave.mockReset();
    mockedUpload.mockReset();
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

  it("shows paste/DnD hint and large preview classes", () => {
    render(
      <StepFeedbackForm
        homeworkId="hw-1"
        position={0}
        title="Разбор шага"
        initial={{
          teacher_text: null,
          teacher_voice_url: null,
          teacher_image_urls: ["/api/uploads/images/existing"],
          published_at: null,
        }}
      />,
    );

    expect(screen.getByText(IMAGE_INTAKE_HINT)).toBeInTheDocument();
    const preview = screen.getByTestId("feedback-preview");
    expect(preview).toHaveClass("object-contain");
    expect(preview).toHaveClass("max-w-full");
    expect(preview.className).not.toMatch(/\bh-20\b/);
    expect(preview.className).not.toMatch(/\bw-20\b/);
  });

  it("pastes images up to remaining slots", async () => {
    mockedUpload.mockImplementation(async (file: File) => ({
      id: `id-${file.name}`,
      url: `/api/uploads/images/${file.name}`,
    }));

    render(
      <StepFeedbackForm
        homeworkId="hw-1"
        position={0}
        title="Разбор шага"
        initial={{
          teacher_text: null,
          teacher_voice_url: null,
          teacher_image_urls: [
            "/api/uploads/images/a",
            "/api/uploads/images/b",
            "/api/uploads/images/c",
            "/api/uploads/images/d",
          ],
          published_at: null,
        }}
      />,
    );

    const files = [
      new File(["1"], "1.png", { type: "image/png" }),
      new File(["2"], "2.png", { type: "image/png" }),
    ];

    fireEvent.paste(screen.getByTestId("feedback-image-intake"), {
      clipboardData: clipboardDataFor(files),
    });

    await waitFor(() => {
      expect(mockedUpload).toHaveBeenCalledTimes(1);
      expect(mockedUpload).toHaveBeenCalledWith(files[0]);
    });

    expect(screen.getByText(/не более 5 фото/i)).toBeInTheDocument();
  });
});
