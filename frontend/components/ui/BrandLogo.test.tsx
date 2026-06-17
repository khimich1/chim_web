import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { BrandLogo } from "@/components/ui/BrandLogo";

describe("BrandLogo", () => {
  it("renders flask svg and label", () => {
    render(<BrandLogo label="Химия" />);
    expect(screen.getByText("Химия")).toBeInTheDocument();
    expect(document.querySelector("svg")).toBeTruthy();
  });

  it("hides decorative svg from assistive tech", () => {
    render(<BrandLogo label="" />);
    const svg = document.querySelector("svg");
    expect(svg?.getAttribute("aria-hidden")).toBe("true");
  });
});
