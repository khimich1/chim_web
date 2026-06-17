import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ProgressBar } from "@/components/tests/ProgressBar";

describe("ProgressBar", () => {
  it("shows step label and percent pill", () => {
    render(<ProgressBar current={2} total={5} />);

    expect(screen.getByText("Шаг 2 из 5")).toBeInTheDocument();
    expect(screen.getByText("40%")).toBeInTheDocument();
  });

  it("exposes progressbar semantics", () => {
    render(<ProgressBar current={3} total={4} />);

    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "3");
    expect(bar).toHaveAttribute("aria-valuemax", "4");
    expect(bar).toHaveAttribute(
      "aria-label",
      "Прогресс: 75%, шаг 3 из 4",
    );
  });

  it("handles zero total safely", () => {
    render(<ProgressBar current={0} total={0} />);

    expect(screen.getByText("Шаг 0 из 0")).toBeInTheDocument();
    expect(screen.getByText("0%")).toBeInTheDocument();
  });
});
