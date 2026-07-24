import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StudentsHub } from "@/components/students/StudentsHub";
import type { Student } from "@/lib/api/types";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}));

vi.mock("@/lib/api/students", () => ({
  createStudent: vi.fn(),
  deleteStudent: vi.fn(),
  resetStudentPassword: vi.fn(),
}));

vi.mock("@/lib/api/templates", () => ({
  assignHomeworkTemplate: vi.fn(),
}));

vi.mock("@/lib/api/groups", () => ({
  listTeacherGroups: vi.fn().mockResolvedValue([]),
  getTeacherGroup: vi.fn(),
  createTeacherGroup: vi.fn(),
  renameTeacherGroup: vi.fn(),
  deleteTeacherGroup: vi.fn(),
  replaceTeacherGroupMembers: vi.fn(),
}));

const students: Student[] = [
  {
    id: "11111111-1111-1111-1111-111111111111",
    email: "student-a",
    track: "ege",
    created_at: "2026-06-01T10:00:00Z",
    first_login_at: null,
    onboarding_completed_at: null,
    is_activated: true,
  },
];

describe("StudentsHub", () => {
  it("shows list tab by default and hides create form", () => {
    render(<StudentsHub students={students} />);

    expect(screen.getByRole("tab", { name: "Ученики" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByText("Список (1)")).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Новый ученик" }),
    ).not.toBeInTheDocument();
  });

  it("shows create form only on Добавить tab", async () => {
    const user = userEvent.setup();
    render(<StudentsHub students={students} />);

    await user.click(screen.getByRole("tab", { name: "Добавить" }));
    expect(
      screen.getByRole("heading", { name: "Новый ученик" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Список (1)")).not.toBeInTheDocument();
  });

  it("shows groups panel on Группы tab", async () => {
    const user = userEvent.setup();
    render(<StudentsHub students={students} />);

    await user.click(screen.getByRole("tab", { name: "Группы" }));
    expect(
      await screen.findByRole("button", { name: "Создать группу" }),
    ).toBeInTheDocument();
  });
});
