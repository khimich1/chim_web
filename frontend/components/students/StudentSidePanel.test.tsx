import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StudentSidePanel } from "@/components/students/StudentSidePanel";
import {
  cancelHomework,
  listHomework,
  restoreHomework,
} from "@/lib/api/homework";
import type { HomeworkAssignment, HomeworkTemplate, Student } from "@/lib/api/types";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn(), replace: vi.fn() }),
}));

vi.mock("@/lib/api/homework", () => ({
  listHomework: vi.fn(),
  cancelHomework: vi.fn(),
  restoreHomework: vi.fn(),
}));

vi.mock("@/lib/api/templates", () => ({
  assignHomeworkTemplate: vi.fn(),
}));

vi.mock("@/lib/api/students", () => ({
  deleteStudent: vi.fn(),
  resetStudentPassword: vi.fn(),
}));

const mockedList = vi.mocked(listHomework);
const mockedCancel = vi.mocked(cancelHomework);
const mockedRestore = vi.mocked(restoreHomework);

const student: Student = {
  id: "s1",
  email: "anna",
  track: "ege",
  created_at: "2026-06-01T10:00:00Z",
  first_login_at: null,
  onboarding_completed_at: null,
  is_activated: true,
};

const templates: HomeworkTemplate[] = [];

const activeHw: HomeworkAssignment = {
  id: "h1",
  student_id: "s1",
  student_email: "anna",
  title: "Алканы",
  description: null,
  due_at: null,
  items: [],
  status: "assigned",
  created_at: "2026-06-20T10:00:00Z",
  submission: null,
  progress: [],
  active_test_session_id: null,
};

beforeEach(() => {
  vi.clearAllMocks();
  mockedList.mockResolvedValue([activeHw]);
  mockedCancel.mockResolvedValue({
    cancelled_ids: ["h1"],
    skipped_submitted_count: 0,
    cancelled_at: "2026-06-20T12:00:00Z",
  });
  mockedRestore.mockResolvedValue({ restored_ids: ["h1"] });
});

describe("StudentSidePanel revoke", () => {
  it("shows trash on active homework and cancels with undo", async () => {
    const user = userEvent.setup();
    render(
      <StudentSidePanel
        student={student}
        templates={templates}
        open
        onClose={vi.fn()}
      />,
    );

    const trash = await screen.findByRole("button", {
      name: 'Отозвать задание «Алканы»',
    });
    await user.click(trash);

    await waitFor(() => {
      expect(mockedCancel).toHaveBeenCalledWith("h1", "single");
    });
    expect(await screen.findByText(/Отозвано: «Алканы»/)).toBeInTheDocument();

    mockedList.mockResolvedValue([
      { ...activeHw, status: "cancelled", cancelled_at: "2026-06-20T12:00:00Z" },
    ]);
    await user.click(screen.getByRole("button", { name: "Вернуть" }));
    await waitFor(() => {
      expect(mockedRestore).toHaveBeenCalledWith("h1", "single");
    });
  });

  it("does not show trash on cancelled rows", async () => {
    mockedList.mockResolvedValue([
      { ...activeHw, status: "cancelled", cancelled_at: "2026-06-20T12:00:00Z" },
    ]);
    render(
      <StudentSidePanel
        student={student}
        templates={templates}
        open
        onClose={vi.fn()}
      />,
    );
    await screen.findByText("Отменено");
    expect(
      screen.queryByRole("button", { name: /Отозвать задание/ }),
    ).not.toBeInTheDocument();
  });
});
