import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { QuestionContent } from "@/components/tests/QuestionContent";

vi.mock("@/lib/api/client", () => ({
  API_URL: "http://localhost:8000",
}));

describe("QuestionContent", () => {
  it("renders formula chips from backticks", () => {
    render(<QuestionContent text="Реакция `CH4` + `O2`" />);

    const formulas = screen.getAllByRole("code");
    expect(formulas).toHaveLength(2);
    expect(formulas[0]).toHaveClass("chem-formula");
    expect(formulas[0]).toHaveTextContent("CH4");
    expect(formulas[1]).toHaveTextContent("O2");
  });

  it("keeps plain text without backticks", () => {
    render(<QuestionContent text="Сколько молей воды?" />);

    expect(screen.getByText("Сколько молей воды?")).toBeInTheDocument();
  });
});
