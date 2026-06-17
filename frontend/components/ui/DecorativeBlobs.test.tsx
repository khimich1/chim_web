import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";

import { DecorativeBlobs } from "@/components/ui/DecorativeBlobs";

describe("DecorativeBlobs", () => {
  it("renders with aria-hidden and pointer-events-none", () => {
    const { container } = render(<DecorativeBlobs />);
    const root = container.firstElementChild;
    expect(root?.getAttribute("aria-hidden")).toBe("true");
    expect(root?.className).toContain("pointer-events-none");
    expect(root?.className).toContain("-z-10");
    expect(root?.querySelectorAll("svg").length).toBeGreaterThanOrEqual(3);
  });
});
