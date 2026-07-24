import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";

import { DecorativeBlobs } from "@/components/ui/DecorativeBlobs";

describe("DecorativeBlobs", () => {
  it("renders with aria-hidden and pointer-events-none", () => {
    const { container } = render(<DecorativeBlobs />);
    const root = container.firstElementChild;
    expect(root?.getAttribute("aria-hidden")).toBe("true");
    expect(root?.className).toContain("pointer-events-none");
    expect(root?.className).toMatch(/\bfixed\b/);
    expect(root?.className).toContain("z-0");
    expect(root?.className).not.toContain("-z-10");
    expect(root?.querySelectorAll("svg").length).toBeGreaterThanOrEqual(3);
  });

  it("marks each svg with a calm-drift class", () => {
    const { container } = render(<DecorativeBlobs />);
    const svgs = container.querySelectorAll("svg");
    expect(svgs.length).toBeGreaterThanOrEqual(3);
    svgs.forEach((svg) => {
      expect(svg.className.baseVal || svg.getAttribute("class") || "").toMatch(
        /chem-blob-drift/,
      );
    });
  });

  it("uses absolute positioning when scoped", () => {
    const { container } = render(<DecorativeBlobs scoped />);
    const root = container.firstElementChild;
    expect(root?.className).toContain("absolute");
    expect(root?.className).toContain("z-0");
    expect(root?.className).not.toContain("-z-10");
    expect(root?.className).not.toMatch(/\bfixed\b/);
  });
});
