import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StepProgressDots } from "@/components/tests/StepProgressDots";
import type { TestStep } from "@/lib/api/types";

function makeStep(overrides: Partial<TestStep> & Pick<TestStep, "position">): TestStep {
  return {
    test_id: overrides.position + 1,
    type: 1,
    question: "Q",
    options: null,
    status: "unseen",
    answer: null,
    is_correct: null,
    hint_used: false,
    ...overrides,
  };
}

describe("StepProgressDots", () => {
  it("renders step count without percent", () => {
    const steps = [
      makeStep({ position: 0, status: "checked", is_correct: true }),
      makeStep({ position: 1 }),
    ];

    render(<StepProgressDots steps={steps} current={1} onSelect={vi.fn()} />);

    expect(screen.getByText("Шаг 2 из 2")).toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });

  it("applies status classes and allows clicking any step", async () => {
    const onSelect = vi.fn();
    const steps = [
      makeStep({ position: 0, status: "checked", is_correct: true }),
      makeStep({ position: 1, status: "answered" }),
      makeStep({ position: 2 }),
    ];

    render(<StepProgressDots steps={steps} current={0} onSelect={onSelect} />);

    const tabs = screen.getAllByRole("tab");
    expect(tabs[0]).toHaveClass("chem-step-dot--correct");
    expect(tabs[0]).toHaveAttribute("aria-current", "step");
    expect(tabs[1]).toHaveClass("chem-step-dot--answered");
    expect(tabs[2]).toHaveClass("chem-step-dot--unseen");
    expect(tabs[2]).not.toBeDisabled();

    await userEvent.click(tabs[1]);
    expect(onSelect).toHaveBeenCalledWith(1);

    await userEvent.click(tabs[2]);
    expect(onSelect).toHaveBeenCalledWith(2);
  });

  it("uses scrollable layout for long sessions", () => {
    const steps = Array.from({ length: 15 }, (_, index) =>
      makeStep({ position: index }),
    );

    const { container } = render(
      <StepProgressDots steps={steps} current={0} onSelect={vi.fn()} />,
    );

    expect(container.querySelector(".chem-step-dots--scroll")).toBeInTheDocument();
  });
});
