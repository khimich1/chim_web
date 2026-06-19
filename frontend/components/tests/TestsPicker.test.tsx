import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TestsPicker } from "@/components/tests/TestsPicker";

vi.mock("@/components/tests/VariantPicker", () => ({
  VariantPicker: () => <div data-testid="variant-picker">variants</div>,
}));

vi.mock("@/components/tests/TaskTypePicker", () => ({
  TaskTypePicker: () => <div data-testid="task-type-picker">task types</div>,
}));

const variants = [{ filename: "001.txt" }];
const taskTypes = [{ type: 1, variant_count: 30 }];

describe("TestsPicker", () => {
  it("shows tabs for EGE and switches to task types", async () => {
    render(
      <TestsPicker variants={variants} taskTypes={taskTypes} track="ege" />,
    );

    expect(screen.getByTestId("variant-picker")).toBeInTheDocument();
    expect(screen.queryByTestId("task-type-picker")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("tab", { name: "По заданиям" }));

    expect(screen.getByTestId("task-type-picker")).toBeInTheDocument();
    expect(screen.queryByTestId("variant-picker")).not.toBeInTheDocument();
  });

  it("hides task type tab for OGE", () => {
    render(
      <TestsPicker variants={variants} taskTypes={taskTypes} track="oge" />,
    );

    expect(screen.queryByRole("tab", { name: "По заданиям" })).not.toBeInTheDocument();
    expect(screen.getByTestId("variant-picker")).toBeInTheDocument();
  });
});
