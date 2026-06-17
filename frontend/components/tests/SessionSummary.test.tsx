import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { SessionSummary } from "@/components/tests/SessionSummary";
import type { TestSession } from "@/lib/api/types";

const session: TestSession = {
  id: "sess-1",
  track: "ege",
  variant_ref: "001.txt",
  homework_assignment_id: null,
  status: "completed",
  score: 2,
  max_score: 3,
  total_steps: 3,
  steps: [
    {
      position: 0,
      test_id: 11,
      type: 1,
      question: "Q1",
      options: null,
      status: "checked",
      answer: "a",
      is_correct: true,
      hint_used: false,
    },
    {
      position: 1,
      test_id: 12,
      type: 2,
      question: "Q2",
      options: null,
      status: "checked",
      answer: "b",
      is_correct: false,
      hint_used: true,
    },
    {
      position: 2,
      test_id: 13,
      type: 3,
      question: "Q3",
      options: null,
      status: "unseen",
      answer: null,
      is_correct: null,
      hint_used: false,
    },
  ],
};

describe("SessionSummary", () => {
  it("renders score and variant title", () => {
    render(<SessionSummary session={session} />);

    expect(screen.getByText("2 / 3")).toBeInTheDocument();
    expect(screen.getByText("67%")).toBeInTheDocument();
    expect(screen.getByText("Вариант 001")).toBeInTheDocument();
  });

  it("shows verdict labels per step", () => {
    render(<SessionSummary session={session} />);

    expect(screen.getByText("✓ Верно")).toBeInTheDocument();
    expect(screen.getByText("✗ Неверно")).toBeInTheDocument();
    expect(screen.getByText("— Не отвечено")).toBeInTheDocument();
    expect(screen.getByText("(с подсказкой)")).toBeInTheDocument();
  });

  it("includes decorative blobs with aria-hidden", () => {
    const { container } = render(<SessionSummary session={session} />);

    const blobs = container.querySelector('[aria-hidden="true"]');
    expect(blobs).toBeTruthy();
    expect(blobs?.querySelectorAll("svg").length).toBeGreaterThanOrEqual(3);
  });

  it("links back to test list", () => {
    render(<SessionSummary session={session} />);

    expect(screen.getByRole("link", { name: "К списку тестов" })).toHaveAttribute(
      "href",
      "/student/tests",
    );
  });
});
