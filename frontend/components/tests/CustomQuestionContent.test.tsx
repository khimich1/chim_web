import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { CustomQuestionContent } from "@/components/tests/CustomQuestionContent";

vi.mock("@/lib/api/client", () => ({
  API_URL: "http://localhost:8000",
}));

describe("CustomQuestionContent", () => {
  it("renders text blocks", () => {
    render(
      <CustomQuestionContent
        blocks={[{ type: "text", content: "Что такое `H2O`?" }]}
      />,
    );

    expect(screen.getByText(/Что такое/)).toBeInTheDocument();
    expect(screen.getByRole("code")).toHaveTextContent("H2O");
  });

  it("shows placeholder when blocks are empty", () => {
    render(<CustomQuestionContent blocks={[]} />);

    expect(screen.getByText("Текст задания отсутствует.")).toBeInTheDocument();
  });
});
