import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { HomeworkSubmissionPhotos } from "@/components/homework/HomeworkSubmissionPhotos";
import type { HomeworkSubmissionStep } from "@/lib/api/types";

vi.mock("@/components/common/AuthenticatedImage", () => ({
  AuthenticatedImage: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} data-testid="authenticated-image" />
  ),
}));

const steps: HomeworkSubmissionStep[] = [
  {
    position: 1,
    custom_task_id: "task-1",
    grading_mode: "self_check",
    answer: "черновик",
    answer_image_urls: [
      "/api/uploads/images/abc-123",
      "/api/uploads/images/abc-456",
    ],
    status: "checked",
  },
];

describe("HomeworkSubmissionPhotos", () => {
  it("renders thumbnails for self_check steps with photos", () => {
    render(<HomeworkSubmissionPhotos steps={steps} />);

    expect(screen.getByText(/Фото письменных ответов/)).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: /Фото ответа к заданию 2, страница 1/ }),
    ).toHaveAttribute("src", "/api/uploads/images/abc-123");
    expect(
      screen.getByRole("img", { name: /Фото ответа к заданию 2, страница 2/ }),
    ).toHaveAttribute("src", "/api/uploads/images/abc-456");
    expect(screen.getByText(/черновик/)).toBeInTheDocument();
  });

  it("renders nothing when no photo URLs", () => {
    const { container } = render(
      <HomeworkSubmissionPhotos
        steps={[
          {
            position: 0,
            custom_task_id: "task-2",
            grading_mode: "self_check",
            answer: null,
            answer_image_urls: [],
            status: "checked",
          },
        ]}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("opens lightbox when a submission photo is clicked", async () => {
    const user = userEvent.setup();
    render(<HomeworkSubmissionPhotos steps={steps} />);

    await user.click(
      screen.getByRole("button", {
        name: /Открыть Фото ответа к заданию 2, страница 2/,
      }),
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("2 из 2")).toBeInTheDocument();
  });
});
