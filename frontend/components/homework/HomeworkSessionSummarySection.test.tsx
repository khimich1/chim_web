import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { HomeworkSessionSummarySection } from "@/components/homework/HomeworkSessionSummarySection";
import type { HomeworkAssignment } from "@/lib/api/types";

vi.mock("@/components/homework/HomeworkSubmitButton", () => ({
  HomeworkSubmitButton: () => <button type="button">Сдать домашнее задание</button>,
}));

vi.mock("@/components/homework/HomeworkReopenButton", () => ({
  HomeworkReopenButton: () => <button type="button">Досдать</button>,
}));

const baseHomework: HomeworkAssignment = {
  id: "hw-1",
  student_id: "student-1",
  student_email: "student@example.com",
  title: "Алканы",
  description: null,
  due_at: null,
  items: [],
  status: "assigned",
  created_at: "2026-01-01T00:00:00Z",
  submission: null,
  progress: [],
  active_test_session_id: null,
};

describe("HomeworkSessionSummarySection", () => {
  it("shows submit button when homework is not submitted", () => {
    render(
      <HomeworkSessionSummarySection
        homeworkId="hw-1"
        sessionId="session-1"
        homework={baseHomework}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Сдать домашнее задание" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "К заданию" })).toHaveAttribute(
      "href",
      "/student/homework/hw-1",
    );
    expect(screen.queryByRole("button", { name: "Досдать" })).not.toBeInTheDocument();
  });

  it("shows reopen button after partial submit", () => {
    render(
      <HomeworkSessionSummarySection
        homeworkId="hw-1"
        sessionId="session-1"
        homework={{
          ...baseHomework,
          status: "submitted",
          can_reopen: true,
          submission: {
            id: "sub-1",
            submitted_at: "2026-01-02T00:00:00Z",
            test_session_id: "session-1",
            score: 1,
            max_score: 2,
            answered_steps: 1,
            total_steps: 2,
            completion_percent: 50,
          },
        }}
      />,
    );

    expect(screen.getByText(/Задание сдано \(1\/2, 50%\)/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Досдать" })).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Сдать домашнее задание" }),
    ).not.toBeInTheDocument();
  });

  it("shows submitted state without reopen when homework is complete", () => {
    render(
      <HomeworkSessionSummarySection
        homeworkId="hw-1"
        sessionId="session-1"
        homework={{
          ...baseHomework,
          status: "submitted",
          can_reopen: false,
          submission: {
            id: "sub-1",
            submitted_at: "2026-01-02T00:00:00Z",
            test_session_id: "session-1",
            score: 2,
            max_score: 2,
            answered_steps: 2,
            total_steps: 2,
            completion_percent: 100,
          },
        }}
      />,
    );

    expect(screen.getByText(/Задание сдано \(2\/2, 100%\)/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Досдать" })).not.toBeInTheDocument();
  });
});
