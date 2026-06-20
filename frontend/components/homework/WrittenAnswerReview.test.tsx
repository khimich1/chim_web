import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { WrittenAnswerReview } from "@/components/homework/WrittenAnswerReview";
import type { HomeworkSubmissionStep } from "@/lib/api/types";

vi.mock("@/components/homework/ImageViewer", () => ({
  ImageViewer: ({ alt }: { alt: string }) => <div data-testid="image-viewer">{alt}</div>,
}));

vi.mock("@/components/tests/CustomQuestionContent", () => ({
  CustomQuestionContent: ({ blocks }: { blocks: { content?: string }[] }) => (
    <div data-testid="question-content">{blocks[0]?.content}</div>
  ),
}));

const step: HomeworkSubmissionStep = {
  position: 0,
  custom_task_id: "task-1",
  title: "Уравнение",
  grading_mode: "self_check",
  question_blocks: [{ type: "text", content: "Решите" }],
  reference_answer: [{ type: "text", content: "x = 2" }],
  answer: "черновик",
  answer_image_url: "/api/uploads/images/abc",
  status: "checked",
};

describe("WrittenAnswerReview", () => {
  it("renders split review layout for self_check steps", () => {
    render(<WrittenAnswerReview steps={[step]} />);

    expect(screen.getByText("Проверка письменных ответов")).toBeInTheDocument();
    expect(screen.getByText("Уравнение")).toBeInTheDocument();
    expect(screen.getByText("Условие")).toBeInTheDocument();
    expect(screen.getByText("Ответ ученика")).toBeInTheDocument();
    expect(screen.getByText("Эталон")).toBeInTheDocument();
    expect(screen.getByTestId("image-viewer")).toBeInTheDocument();
    expect(screen.getByText("x = 2")).toBeInTheDocument();
  });

  it("renders nothing without photo steps", () => {
    const { container } = render(
      <WrittenAnswerReview
        steps={[{ ...step, answer_image_url: null }]}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});
