import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TaskTypePicker } from "@/components/tests/TaskTypePicker";
import { createSession, getActiveSession } from "@/lib/api/tests";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/lib/api/tests", () => ({
  createSession: vi.fn(),
  getActiveSession: vi.fn(),
}));

const mockedCreate = vi.mocked(createSession);
const mockedActive = vi.mocked(getActiveSession);

const taskTypes = [
  { type: 1, variant_count: 30 },
  { type: 2, variant_count: 30 },
];

beforeEach(() => {
  vi.clearAllMocks();
  mockedActive.mockResolvedValue({ session_id: null });
});

describe("TaskTypePicker", () => {
  it("shows continue for task types with active sessions", async () => {
    mockedActive.mockImplementation(async ({ taskType }) => ({
      session_id: taskType === 1 ? "sess-1" : null,
    }));

    render(<TaskTypePicker taskTypes={taskTypes} />);

    expect(await screen.findByRole("button", { name: "Продолжить" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Начать" })).toBeInTheDocument();
    expect(screen.getByText("Задание 1")).toBeInTheDocument();
  });

  it("starts a session by task type", async () => {
    mockedCreate.mockResolvedValue({
      id: "sess-new",
      track: "ege",
      variant_ref: null,
      homework_assignment_id: null,
      status: "in_progress",
      score: null,
      max_score: null,
      total_steps: 30,
      steps: [],
      created_at: "2026-01-01T00:00:00Z",
    });

    render(<TaskTypePicker taskTypes={[taskTypes[0]]} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Начать" })).toBeEnabled();
    });

    await userEvent.click(screen.getByRole("button", { name: "Начать" }));

    expect(mockedCreate).toHaveBeenCalledWith({ types: [1] });
    expect(push).toHaveBeenCalledWith("/student/tests/sessions/sess-new");
  });
});
