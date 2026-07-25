import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { WrittenAnswerReview } from "@/components/homework/WrittenAnswerReview";
import type { HomeworkSubmissionStep } from "@/lib/api/types";

vi.mock("@/components/homework/ImageViewer", () => ({
  ImageViewer: ({
    alt,
    onExpand,
  }: {
    alt: string;
    onExpand?: () => void;
  }) => (
    <div data-testid="image-viewer">
      <span>{alt}</span>
      {onExpand ? (
        <button type="button" onClick={onExpand} aria-label="Открыть на весь экран">
          expand
        </button>
      ) : null}
    </div>
  ),
}));

vi.mock("@/components/homework/StepFeedbackForm", () => ({
  StepFeedbackForm: ({ title }: { title: string }) => (
    <div data-testid="feedback-form">{title}</div>
  ),
}));

vi.mock("@/components/tests/CustomQuestionContent", () => ({
  CustomQuestionContent: ({
    blocks,
    onImageClick,
  }: {
    blocks: { type?: string; content?: string; url?: string }[];
    onImageClick?: (
      items: { src: string; alt: string }[],
      index: number,
    ) => void;
  }) => {
    const images = blocks.filter((b) => b.type === "image" && b.url);
    if (images.length > 0 && onImageClick) {
      return (
        <div data-testid="question-content">
          {images.map((block, index) => (
            <button
              key={block.url}
              type="button"
              aria-label={`Открыть иллюстрацию ${index + 1}`}
              onClick={() =>
                onImageClick(
                  images.map((img) => ({
                    src: img.url!,
                    alt: "Иллюстрация к заданию",
                  })),
                  index,
                )
              }
            >
              img {index + 1}
            </button>
          ))}
        </div>
      );
    }
    return <div data-testid="question-content">{blocks[0]?.content}</div>;
  },
}));

vi.mock("@/components/common/AuthenticatedImage", () => ({
  AuthenticatedImage: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} />
  ),
}));

vi.mock("@/components/common/ImageLightbox", () => ({
  ImageLightbox: ({
    open,
    items,
    index,
    onClose,
  }: {
    open: boolean;
    items: { src: string; alt: string }[];
    index: number;
    onClose: () => void;
  }) =>
    open ? (
      <div role="dialog" aria-modal="true">
        <p data-testid="lightbox-src">{items[index]?.src}</p>
        <p data-testid="lightbox-count">
          {items.length > 1 ? `${index + 1} из ${items.length}` : "single"}
        </p>
        <button type="button" onClick={onClose} aria-label="Закрыть">
          close
        </button>
      </div>
    ) : null,
}));

const step: HomeworkSubmissionStep = {
  position: 0,
  custom_task_id: "task-1",
  title: "Уравнение",
  grading_mode: "self_check",
  question_blocks: [{ type: "text", content: "Решите" }],
  reference_answer: [{ type: "text", content: "x = 2" }],
  answer: "черновик",
  answer_image_urls: ["/api/uploads/images/abc"],
  status: "checked",
};

describe("WrittenAnswerReview", () => {
  it("renders split review layout for self_check steps", () => {
    render(<WrittenAnswerReview homeworkId="hw-1" steps={[step]} />);

    expect(screen.getByText("Проверка письменных ответов")).toBeInTheDocument();
    expect(screen.getByText("Уравнение")).toBeInTheDocument();
    expect(screen.getByText("Условие")).toBeInTheDocument();
    expect(screen.getByText("Ответ ученика")).toBeInTheDocument();
    expect(screen.getByText("Эталон")).toBeInTheDocument();
    expect(screen.getByTestId("image-viewer")).toBeInTheDocument();
    expect(screen.getByText("x = 2")).toBeInTheDocument();
    expect(screen.getAllByTestId("feedback-form")).toHaveLength(2);
    expect(screen.getByText("Общий комментарий к сдаче")).toBeInTheDocument();
  });

  it("renders all pages for multi-photo steps", () => {
    render(
      <WrittenAnswerReview
        homeworkId="hw-1"
        steps={[
          {
            ...step,
            answer_image_urls: [
              "/api/uploads/images/a",
              "/api/uploads/images/b",
            ],
          },
        ]}
      />,
    );

    expect(screen.getByText("Страница 1")).toBeInTheDocument();
    expect(screen.getByText("Страница 2")).toBeInTheDocument();
    expect(screen.getAllByTestId("image-viewer")).toHaveLength(2);
  });

  it("renders nothing without photo steps", () => {
    const { container } = render(
      <WrittenAnswerReview
        homeworkId="hw-1"
        steps={[{ ...step, answer_image_urls: [] }]}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("opens lightbox from condition image with sibling gallery", async () => {
    const user = userEvent.setup();
    render(
      <WrittenAnswerReview
        homeworkId="hw-1"
        steps={[
          {
            ...step,
            question_blocks: [
              { type: "image", url: "/api/uploads/images/q1" },
              { type: "image", url: "/api/uploads/images/q2" },
            ],
          },
        ]}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Открыть иллюстрацию 2" }),
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByTestId("lightbox-src")).toHaveTextContent(
      "/api/uploads/images/q2",
    );
    expect(screen.getByTestId("lightbox-count")).toHaveTextContent("2 из 2");
  });

  it("opens lightbox from answer expand and feedback thumb", async () => {
    const user = userEvent.setup();
    render(
      <WrittenAnswerReview
        homeworkId="hw-1"
        steps={[
          {
            ...step,
            answer_image_urls: [
              "/api/uploads/images/a",
              "/api/uploads/images/b",
            ],
            feedback: {
              teacher_text: "ok",
              teacher_voice_url: null,
              teacher_image_urls: [
                "/api/uploads/images/f1",
                "/api/uploads/images/f2",
              ],
            },
          },
        ]}
      />,
    );

    await user.click(
      screen.getAllByRole("button", { name: "Открыть на весь экран" })[1]!,
    );
    expect(screen.getByTestId("lightbox-src")).toHaveTextContent(
      "/api/uploads/images/b",
    );
    expect(screen.getByTestId("lightbox-count")).toHaveTextContent("2 из 2");

    await user.click(screen.getByRole("button", { name: "Закрыть" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Открыть фото разбора 1" }),
    );
    expect(screen.getByTestId("lightbox-src")).toHaveTextContent(
      "/api/uploads/images/f1",
    );
    expect(screen.getByTestId("lightbox-count")).toHaveTextContent("1 из 2");
  });
});
