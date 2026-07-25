import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ImageViewer } from "@/components/homework/ImageViewer";

vi.mock("@/components/common/AuthenticatedImage", () => ({
  AuthenticatedImage: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} data-testid="viewer-image" />
  ),
}));

function firePointer(
  target: Element,
  type: "pointerDown" | "pointerMove" | "pointerUp",
  clientX: number,
  clientY: number,
) {
  const event = new Event(type.toLowerCase(), { bubbles: true, cancelable: true });
  Object.defineProperties(event, {
    clientX: { value: clientX },
    clientY: { value: clientY },
    pointerId: { value: 1 },
  });
  fireEvent(target, event);
}

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

  it("hides expand control when onExpand is omitted", () => {
    render(<ImageViewer src="/api/uploads/images/1" alt="Student work" />);

    expect(
      screen.queryByRole("button", { name: "Открыть на весь экран" }),
    ).not.toBeInTheDocument();
  });

  it("calls onExpand when expand icon is clicked", async () => {
    const user = userEvent.setup();
    const onExpand = vi.fn();
    render(
      <ImageViewer
        src="/api/uploads/images/1"
        alt="Student work"
        onExpand={onExpand}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Открыть на весь экран" }),
    );
    expect(onExpand).toHaveBeenCalledTimes(1);
  });

  it("calls onExpand on click without drag", () => {
    const onExpand = vi.fn();
    render(
      <ImageViewer
        src="/api/uploads/images/1"
        alt="Student work"
        onExpand={onExpand}
      />,
    );

    const stage = screen.getByRole("region", { name: "Student work" });
    firePointer(stage, "pointerDown", 100, 100);
    firePointer(stage, "pointerMove", 102, 101);
    firePointer(stage, "pointerUp", 102, 101);

    expect(onExpand).toHaveBeenCalledTimes(1);
  });

  it("does not call onExpand when pointer was dragged", () => {
    const onExpand = vi.fn();
    render(
      <ImageViewer
        src="/api/uploads/images/1"
        alt="Student work"
        onExpand={onExpand}
      />,
    );

    const stage = screen.getByRole("region", { name: "Student work" });
    firePointer(stage, "pointerDown", 100, 100);
    firePointer(stage, "pointerMove", 120, 110);
    firePointer(stage, "pointerUp", 120, 110);

    expect(onExpand).not.toHaveBeenCalled();
  });
});
