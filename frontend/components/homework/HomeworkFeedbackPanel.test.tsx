import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { HomeworkFeedbackPanel } from "@/components/homework/HomeworkFeedbackPanel";

vi.mock("@/lib/api/homework-feedback", () => ({
  getStudentHomeworkFeedback: vi.fn(),
}));

vi.mock("@/components/homework/AuthenticatedAudio", () => ({
  AuthenticatedAudio: () => <div>audio</div>,
}));

vi.mock("@/components/common/AuthenticatedImage", () => ({
  AuthenticatedImage: ({ alt }: { alt: string }) => <div>{alt}</div>,
}));

import { getStudentHomeworkFeedback } from "@/lib/api/homework-feedback";

const mockedGet = vi.mocked(getStudentHomeworkFeedback);

describe("HomeworkFeedbackPanel", () => {
  it("renders teacher feedback for student", async () => {
    mockedGet.mockResolvedValue({
      has_feedback: true,
      steps: [
        {
          position: 0,
          title: "Уравнение",
          teacher_text: "Проверьте знаки",
          teacher_voice_url: null,
          teacher_image_urls: [],
          published_at: "2026-06-20T12:00:00Z",
        },
      ],
      submission: null,
    });

    render(<HomeworkFeedbackPanel homeworkId="hw-1" />);

    await waitFor(() => {
      expect(screen.getByText("Разбор преподавателя")).toBeInTheDocument();
    });
    expect(screen.getByText("Проверьте знаки")).toBeInTheDocument();
  });

  it("opens lightbox from feedback thumb", async () => {
    const user = userEvent.setup();
    mockedGet.mockResolvedValue({
      has_feedback: true,
      steps: [
        {
          position: 0,
          title: "Уравнение",
          teacher_text: null,
          teacher_voice_url: null,
          teacher_image_urls: [
            "/api/uploads/images/f1",
            "/api/uploads/images/f2",
          ],
          published_at: "2026-06-20T12:00:00Z",
        },
      ],
      submission: null,
    });

    render(<HomeworkFeedbackPanel homeworkId="hw-1" />);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Открыть Фото разбора 1" }),
      ).toBeInTheDocument();
    });

    await user.click(
      screen.getByRole("button", { name: "Открыть Фото разбора 2" }),
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("2 из 2")).toBeInTheDocument();
  });
});
