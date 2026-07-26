import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { StepFeedbackForm } from "@/components/homework/StepFeedbackForm";
import { ApiError } from "@/lib/api/client";
import { createFeedbackHandoff, getCaptureMeta } from "@/lib/api/handoff";
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

vi.mock("@/lib/api/handoff", () => ({
  createFeedbackHandoff: vi.fn(),
  getCaptureMeta: vi.fn(),
}));

vi.mock("react-qr-code", () => ({
  default: ({ value }: { value: string }) => (
    <div data-testid="feedback-qr">{value}</div>
  ),
}));

vi.mock("@/components/homework/VoiceRecorder", () => ({
  VoiceRecorder: ({
    onRecorded,
    variant = "button",
  }: {
    onRecorded: (file: File, durationSec: number) => void;
    variant?: "button" | "icon";
  }) =>
    variant === "icon" ? (
      <button
        type="button"
        aria-label="Записать голос"
        onClick={() =>
          onRecorded(new File(["audio"], "voice.webm", { type: "audio/webm" }), 5)
        }
      >
        mic
      </button>
    ) : (
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
const mockedCreateHandoff = vi.mocked(createFeedbackHandoff);
const mockedGetMeta = vi.mocked(getCaptureMeta);

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
    mockedCreateHandoff.mockReset();
    mockedGetMeta.mockReset();
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
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
    fireEvent.click(screen.getByRole("button", { name: "Сохранить" }));

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

    expect(screen.getByRole("button", { name: "Сохранить" })).toBeDisabled();
  });

  it("shows composer sheet with mic and Save on the right", () => {
    render(
      <StepFeedbackForm
        homeworkId="hw-1"
        position={0}
        title="Разбор шага"
      />,
    );

    expect(screen.queryByText("Текстовый комментарий")).not.toBeInTheDocument();
    expect(screen.queryByText("Голосовой комментарий")).not.toBeInTheDocument();
    expect(screen.queryByText("Записать голос")).not.toBeInTheDocument();
    expect(screen.queryByText("Сохранить разбор")).not.toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Записать голос" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Сохранить" })).toBeInTheDocument();
    expect(screen.getByLabelText(/Прикрепить с этого устройства/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Сфотографировать с телефона" }),
    ).toBeInTheDocument();
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

  it("uploads from device button into preview and allows remove", async () => {
    mockedUpload.mockResolvedValue({
      id: "img-1",
      url: "/api/uploads/images/img-1",
    });

    render(
      <StepFeedbackForm
        homeworkId="hw-1"
        position={0}
        title="Разбор шага"
      />,
    );

    const fileInput = screen.getByLabelText(/Прикрепить с этого устройства/i);
    const file = new File(["photo"], "photo.png", { type: "image/png" });
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockedUpload).toHaveBeenCalledWith(file);
      expect(screen.getByTestId("feedback-preview")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Удалить фото" }));
    expect(screen.queryByTestId("feedback-preview")).not.toBeInTheDocument();
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

  it("creates feedback handoff QR and polls staged photo into gallery", async () => {
    mockedCreateHandoff.mockResolvedValue({
      token: "tok-fb-1",
      capture_url: "http://localhost:3000/student/capture/tok-fb-1",
      expires_at: "2026-07-25T12:00:00Z",
    });
    mockedGetMeta
      .mockResolvedValueOnce({
        purpose: "feedback",
        homework_id: "hw-1",
        position: 0,
        task_title: "Фото к разбору",
        question_preview: "hint",
        expires_at: "2026-07-25T12:00:00Z",
        already_has_photo: false,
        staged_image_id: null,
        staged_image_url: null,
      })
      .mockResolvedValueOnce({
        purpose: "feedback",
        homework_id: "hw-1",
        position: 0,
        task_title: "Фото к разбору",
        question_preview: "hint",
        expires_at: "2026-07-25T12:00:00Z",
        already_has_photo: true,
        staged_image_id: "staged-1",
        staged_image_url: "/api/uploads/images/staged-1",
      });

    render(
      <StepFeedbackForm
        homeworkId="hw-1"
        position={0}
        title="Разбор шага"
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Сфотографировать с телефона" }),
    );

    await waitFor(() => {
      expect(mockedCreateHandoff).toHaveBeenCalledWith("hw-1", 0);
      expect(screen.getByTestId("feedback-qr")).toHaveTextContent(
        "/student/capture/tok-fb-1",
      );
    });

    await waitFor(() => {
      expect(mockedGetMeta).toHaveBeenCalled();
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2600);
    });

    await waitFor(() => {
      expect(screen.getByTestId("feedback-preview")).toBeInTheDocument();
    });

    expect(screen.queryByTestId("feedback-qr")).not.toBeInTheDocument();
    expect(mockedSave).not.toHaveBeenCalled();
  });

  it("stops polling and shows error when handoff is gone (410)", async () => {
    mockedCreateHandoff.mockResolvedValue({
      token: "tok-expired",
      capture_url: "http://localhost:3000/student/capture/tok-expired",
      expires_at: "2026-07-25T12:00:00Z",
    });
    mockedGetMeta.mockRejectedValue(new ApiError(410, "Handoff token expired"));

    render(
      <StepFeedbackForm
        homeworkId="hw-1"
        position={0}
        title="Разбор шага"
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Сфотографировать с телефона" }),
    );

    await waitFor(() => {
      expect(screen.getByTestId("feedback-qr")).toBeInTheDocument();
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });

    await waitFor(() => {
      expect(screen.getByText(/истекла/i)).toBeInTheDocument();
    });
    expect(screen.queryByTestId("feedback-qr")).not.toBeInTheDocument();
    expect(screen.queryByText(/Ожидание фото/)).not.toBeInTheDocument();
  });

  it("appends polled staged photo up to feedback image limit then clears QR", async () => {
    mockedCreateHandoff.mockResolvedValue({
      token: "tok-near-full",
      capture_url: "http://localhost:3000/student/capture/tok-near-full",
      expires_at: "2026-07-25T12:00:00Z",
    });
    mockedGetMeta.mockResolvedValue({
      purpose: "feedback",
      homework_id: "hw-1",
      position: 0,
      task_title: "Фото к разбору",
      question_preview: "hint",
      expires_at: "2026-07-25T12:00:00Z",
      already_has_photo: true,
      staged_image_id: "staged-last",
      staged_image_url: "/api/uploads/images/staged-last",
    });

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

    fireEvent.click(
      screen.getByRole("button", { name: "Сфотографировать с телефона" }),
    );

    await waitFor(() => {
      expect(screen.getByTestId("feedback-qr")).toBeInTheDocument();
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });

    await waitFor(() => {
      expect(screen.getAllByTestId("feedback-preview")).toHaveLength(5);
    });
    expect(screen.queryByTestId("feedback-qr")).not.toBeInTheDocument();
    expect(screen.getByText(/Достигнут лимит 5 фото/i)).toBeInTheDocument();
  });

  it("clears QR waiting UI when slots fill while polling", async () => {
    mockedCreateHandoff.mockResolvedValue({
      token: "tok-race",
      capture_url: "http://localhost:3000/student/capture/tok-race",
      expires_at: "2026-07-25T12:00:00Z",
    });
    mockedGetMeta.mockResolvedValue({
      purpose: "feedback",
      homework_id: "hw-1",
      position: 0,
      task_title: "Фото к разбору",
      question_preview: "hint",
      expires_at: "2026-07-25T12:00:00Z",
      already_has_photo: false,
      staged_image_id: null,
      staged_image_url: null,
    });
    mockedUpload.mockResolvedValue({
      id: "img-fill",
      url: "/api/uploads/images/img-fill",
    });

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

    fireEvent.click(
      screen.getByRole("button", { name: "Сфотографировать с телефона" }),
    );

    await waitFor(() => {
      expect(screen.getByTestId("feedback-qr")).toBeInTheDocument();
      expect(screen.getByText(/Ожидание фото/)).toBeInTheDocument();
    });

    const fileInput = screen.getByLabelText(/Прикрепить с этого устройства/i);
    fireEvent.change(fileInput, {
      target: { files: [new File(["x"], "fill.png", { type: "image/png" })] },
    });

    await waitFor(() => {
      expect(screen.getByText(/Достигнут лимит 5 фото/i)).toBeInTheDocument();
      expect(screen.queryByTestId("feedback-qr")).not.toBeInTheDocument();
      expect(screen.queryByText(/Ожидание фото/)).not.toBeInTheDocument();
    });
  });

  it("opens lightbox from draft preview before save", async () => {
    const user = userEvent.setup();
    render(
      <StepFeedbackForm
        homeworkId="hw-1"
        position={0}
        title="Разбор шага"
        initial={{
          teacher_text: null,
          teacher_voice_url: null,
          teacher_image_urls: [
            "/api/uploads/images/d1",
            "/api/uploads/images/d2",
          ],
          published_at: null,
        }}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Открыть Фото разбора 2" }),
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("2 из 2")).toBeInTheDocument();
  });
});
