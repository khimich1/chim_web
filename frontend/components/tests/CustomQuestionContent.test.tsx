import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CustomQuestionContent } from "@/components/tests/CustomQuestionContent";

vi.mock("@/lib/api/client", () => ({
  API_URL: "http://localhost:8000",
}));

vi.mock("@/components/common/AuthenticatedImage", () => ({
  AuthenticatedImage: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} />
  ),
}));

describe("CustomQuestionContent", () => {
  it("renders text blocks", () => {
    render(
      <CustomQuestionContent
        blocks={[{ type: "text", content: "Что такое `H2O`?" }]}
      />,
    );

    expect(screen.getByText(/Что такое/)).toBeInTheDocument();
    expect(screen.getByRole("code")).toHaveTextContent("H2O");
  });

  it("shows placeholder when blocks are empty", () => {
    render(<CustomQuestionContent blocks={[]} />);

    expect(screen.getByText("Текст задания отсутствует.")).toBeInTheDocument();
  });

  it("calls onImageClick with all image siblings and clicked index", async () => {
    const user = userEvent.setup();
    const onImageClick = vi.fn();

    render(
      <CustomQuestionContent
        blocks={[
          { type: "text", content: "Условие" },
          { type: "image", url: "/api/uploads/images/1" },
          { type: "image", url: "/api/uploads/images/2" },
        ]}
        onImageClick={onImageClick}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Открыть иллюстрацию 2" }),
    );

    expect(onImageClick).toHaveBeenCalledWith(
      [
        { src: "/api/uploads/images/1", alt: "Иллюстрация к заданию" },
        { src: "/api/uploads/images/2", alt: "Иллюстрация к заданию" },
      ],
      1,
    );
  });

  it("passes a single-item list when only one image block exists", async () => {
    const user = userEvent.setup();
    const onImageClick = vi.fn();

    render(
      <CustomQuestionContent
        blocks={[{ type: "image", url: "/api/uploads/images/only" }]}
        onImageClick={onImageClick}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Открыть иллюстрацию 1" }),
    );

    expect(onImageClick).toHaveBeenCalledWith(
      [{ src: "/api/uploads/images/only", alt: "Иллюстрация к заданию" }],
      0,
    );
  });

  it("does not throw when onImageClick is omitted", async () => {
    const user = userEvent.setup();

    render(
      <CustomQuestionContent
        blocks={[{ type: "image", url: "/api/uploads/images/1" }]}
      />,
    );

    await expect(
      user.click(screen.getByRole("img", { name: "Иллюстрация к заданию" })),
    ).resolves.not.toThrow();
  });
});
