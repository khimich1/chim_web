import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ImageViewer } from "@/components/homework/ImageViewer";

vi.mock("@/components/common/AuthenticatedImage", () => ({
  AuthenticatedImage: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} data-testid="viewer-image" />
  ),
}));

describe("ImageViewer", () => {
  it("renders controls and image", () => {
    render(<ImageViewer src="/api/uploads/images/1" alt="Student work" />);

    expect(screen.getByRole("button", { name: "↻ 90°" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Сброс" })).toBeInTheDocument();
    expect(screen.getByTestId("viewer-image")).toHaveAttribute(
      "src",
      "/api/uploads/images/1",
    );
  });

  it("rotates image transform on button click", async () => {
    const user = userEvent.setup();
    render(<ImageViewer src="/api/uploads/images/1" alt="Student work" />);

    const wrapper = screen.getByRole("region", { name: "Student work" })
      .firstElementChild as HTMLElement;

    expect(wrapper.style.transform).toContain("rotate(0deg)");

    await user.click(screen.getByRole("button", { name: "↻ 90°" }));
    expect(wrapper.style.transform).toContain("rotate(90deg)");
  });
});
