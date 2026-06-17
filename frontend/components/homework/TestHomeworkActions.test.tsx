import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TestHomeworkActions } from "@/components/homework/TestHomeworkActions";
import { createHomeworkTestSession } from "@/lib/api/tests";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/lib/api/tests", () => ({
  createHomeworkTestSession: vi.fn(),
}));

const mockedCreate = vi.mocked(createHomeworkTestSession);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("TestHomeworkActions", () => {
  it("shows start button when there is no active session", () => {
    render(<TestHomeworkActions homeworkId="hw-1" />);

    expect(
      screen.getByRole("button", { name: "Начать тест" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Продолжить тест" }),
    ).not.toBeInTheDocument();
  });

  it("shows continue button when active session exists", async () => {
    render(
      <TestHomeworkActions
        homeworkId="hw-1"
        activeTestSessionId="sess-42"
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Продолжить тест" }),
    );

    expect(push).toHaveBeenCalledWith("/student/tests/sessions/sess-42");
    expect(mockedCreate).not.toHaveBeenCalled();
  });

  it("starts a new session when no active session", async () => {
    mockedCreate.mockResolvedValue({
      id: "sess-new",
      track: "ege",
      variant_ref: null,
      homework_assignment_id: "hw-1",
      status: "in_progress",
      score: null,
      max_score: null,
      total_steps: 1,
      steps: [],
    });

    render(<TestHomeworkActions homeworkId="hw-1" />);

    await userEvent.click(screen.getByRole("button", { name: "Начать тест" }));

    expect(mockedCreate).toHaveBeenCalledWith("hw-1");
    expect(push).toHaveBeenCalledWith("/student/tests/sessions/sess-new");
  });
});
