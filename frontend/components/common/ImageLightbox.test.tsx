import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { ImageLightbox } from "@/components/common/ImageLightbox";

vi.mock("@/components/common/AuthenticatedImage", () => ({
  AuthenticatedImage: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} data-testid="lightbox-image" />
  ),
}));

const items = [
  { src: "/api/uploads/images/a", alt: "Фото A" },
  { src: "/api/uploads/images/b", alt: "Фото B" },
];

describe("ImageLightbox", () => {
  it("renders nothing when closed", () => {
    const { container } = render(
      <ImageLightbox
        open={false}
        items={items}
        index={0}
        onClose={vi.fn()}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing when items are empty", () => {
    const { container } = render(
      <ImageLightbox open items={[]} index={0} onClose={vi.fn()} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("opens as dialog with image and close control", () => {
    render(
      <ImageLightbox
        open
        items={[{ src: "/api/uploads/images/a", alt: "Фото A" }]}
        index={0}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "true");
    expect(screen.getByTestId("lightbox-image")).toHaveAttribute(
      "src",
      "/api/uploads/images/a",
    );
    expect(screen.getByRole("button", { name: "Закрыть" })).toBeInTheDocument();
  });

  it("closes on Esc and backdrop click", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <ImageLightbox
        open
        items={[{ src: "/api/uploads/images/a", alt: "Фото A" }]}
        index={0}
        onClose={onClose}
      />,
    );

    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);

    onClose.mockClear();
    await user.click(screen.getByRole("button", { name: "Закрыть фон" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("zooms and rotates via controls", async () => {
    const user = userEvent.setup();
    render(
      <ImageLightbox
        open
        items={[{ src: "/api/uploads/images/a", alt: "Фото A" }]}
        index={0}
        onClose={vi.fn()}
      />,
    );

    const stage = screen.getByRole("region", { name: "Фото A" });
    const wrapper = stage.firstElementChild as HTMLElement;

    expect(wrapper.style.transform).toContain("scale(1)");
    expect(wrapper.style.transform).toContain("rotate(0deg)");

    await user.click(screen.getByRole("button", { name: "Увеличить" }));
    expect(wrapper.style.transform).toContain("scale(1.25)");

    await user.click(screen.getByRole("button", { name: "Уменьшить" }));
    expect(wrapper.style.transform).toContain("scale(1)");

    await user.click(screen.getByRole("button", { name: "↻ 90°" }));
    expect(wrapper.style.transform).toContain("rotate(90deg)");

    await user.click(screen.getByRole("button", { name: "Сброс" }));
    expect(wrapper.style.transform).toContain("scale(1)");
    expect(wrapper.style.transform).toContain("rotate(0deg)");
  });

  it("shows gallery nav and counter when multiple items", async () => {
    const user = userEvent.setup();
    const onIndexChange = vi.fn();
    render(
      <ImageLightbox
        open
        items={items}
        index={0}
        onClose={vi.fn()}
        onIndexChange={onIndexChange}
      />,
    );

    expect(screen.getByText("1 из 2")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Предыдущее" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Следующее" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Следующее" }));
    expect(onIndexChange).toHaveBeenCalledWith(1);
  });

  it("hides gallery nav for a single item", () => {
    render(
      <ImageLightbox
        open
        items={[{ src: "/api/uploads/images/a", alt: "Фото A" }]}
        index={0}
        onClose={vi.fn()}
      />,
    );

    expect(screen.queryByText(/из/)).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Предыдущее" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Следующее" }),
    ).not.toBeInTheDocument();
  });

  it("navigates gallery with arrow keys and clamps at edges", async () => {
    const user = userEvent.setup();
    const onIndexChange = vi.fn();
    const { rerender } = render(
      <ImageLightbox
        open
        items={items}
        index={0}
        onClose={vi.fn()}
        onIndexChange={onIndexChange}
      />,
    );

    await user.keyboard("{ArrowLeft}");
    expect(onIndexChange).not.toHaveBeenCalled();

    await user.keyboard("{ArrowRight}");
    expect(onIndexChange).toHaveBeenCalledWith(1);

    onIndexChange.mockClear();
    rerender(
      <ImageLightbox
        open
        items={items}
        index={1}
        onClose={vi.fn()}
        onIndexChange={onIndexChange}
      />,
    );

    await user.keyboard("{ArrowRight}");
    expect(onIndexChange).not.toHaveBeenCalled();

    await user.keyboard("{ArrowLeft}");
    expect(onIndexChange).toHaveBeenCalledWith(0);
  });

  it("resets transform when index changes", async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <ImageLightbox
        open
        items={items}
        index={0}
        onClose={vi.fn()}
        onIndexChange={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Увеличить" }));
    await user.click(screen.getByRole("button", { name: "↻ 90°" }));

    let stage = screen.getByRole("region", { name: "Фото A" });
    let wrapper = stage.firstElementChild as HTMLElement;
    expect(wrapper.style.transform).toContain("scale(1.25)");
    expect(wrapper.style.transform).toContain("rotate(90deg)");

    rerender(
      <ImageLightbox
        open
        items={items}
        index={1}
        onClose={vi.fn()}
        onIndexChange={vi.fn()}
      />,
    );

    stage = screen.getByRole("region", { name: "Фото B" });
    wrapper = stage.firstElementChild as HTMLElement;
    expect(wrapper.style.transform).toContain("scale(1)");
    expect(wrapper.style.transform).toContain("rotate(0deg)");
  });

  it("traps Tab focus within the dialog", async () => {
    const user = userEvent.setup();
    render(
      <ImageLightbox
        open
        items={[{ src: "/api/uploads/images/a", alt: "Фото A" }]}
        index={0}
        onClose={vi.fn()}
      />,
    );

    const closeBtn = screen.getByRole("button", { name: "Закрыть" });
    expect(closeBtn).toHaveFocus();

    const zoomOut = screen.getByRole("button", { name: "Уменьшить" });
    const zoomIn = screen.getByRole("button", { name: "Увеличить" });
    const rotate = screen.getByRole("button", { name: "↻ 90°" });
    const reset = screen.getByRole("button", { name: "Сброс" });

    await user.tab();
    expect(zoomOut).toHaveFocus();
    await user.tab();
    expect(zoomIn).toHaveFocus();
    await user.tab();
    expect(rotate).toHaveFocus();
    await user.tab();
    expect(reset).toHaveFocus();
    await user.tab();
    expect(closeBtn).toHaveFocus();

    await user.tab({ shift: true });
    expect(reset).toHaveFocus();
  });

  it("returns focus to the trigger element on close", async () => {
    const user = userEvent.setup();
    function Harness() {
      const [open, setOpen] = useState(false);
      return (
        <div>
          <button type="button" onClick={() => setOpen(true)}>
            Открыть превью
          </button>
          <ImageLightbox
            open={open}
            items={[{ src: "/api/uploads/images/a", alt: "Фото A" }]}
            index={0}
            onClose={() => setOpen(false)}
          />
        </div>
      );
    }

    render(<Harness />);
    const trigger = screen.getByRole("button", { name: "Открыть превью" });
    await user.click(trigger);
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
  });
});
