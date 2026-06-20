import { render, screen } from "@testing-library/react";
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
    answer_image_url: "/api/uploads/images/abc-123",
    status: "checked",
  },
];

describe("HomeworkSubmissionPhotos", () => {
  it("renders thumbnails for self_check steps with photos", () => {
    render(<HomeworkSubmissionPhotos steps={steps} />);

    expect(screen.getByText(/Фото письменных ответов/)).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Фото ответа к заданию 2/ })).toHaveAttribute(
      "src",
      "/api/uploads/images/abc-123",
    );
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
            answer_image_url: null,
            status: "checked",
          },
        ]}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});
