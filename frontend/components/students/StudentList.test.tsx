import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StudentList } from "@/components/students/StudentList";
import { listHomework } from "@/lib/api/homework";
import {
  deleteStudent,
  resetStudentPassword,
} from "@/lib/api/students";
import { assignHomeworkTemplate } from "@/lib/api/templates";
import type {
  HomeworkAssignment,
  HomeworkTemplate,
  Student,
  TeacherStudentStats,
} from "@/lib/api/types";

const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

vi.mock("@/lib/api/students", () => ({
  deleteStudent: vi.fn(),
  resetStudentPassword: vi.fn(),
}));

vi.mock("@/lib/api/templates", () => ({
  assignHomeworkTemplate: vi.fn(),
}));

vi.mock("@/lib/api/homework", () => ({
  listHomework: vi.fn(),
}));

const mockedDelete = vi.mocked(deleteStudent);
const mockedReset = vi.mocked(resetStudentPassword);
const mockedAssign = vi.mocked(assignHomeworkTemplate);
const mockedListHomework = vi.mocked(listHomework);

const students: Student[] = [
  {
    id: "11111111-1111-1111-1111-111111111111",
    email: "student-a",
    track: "ege",
    created_at: "2026-06-01T10:00:00Z",
    first_login_at: null,
    onboarding_completed_at: null,
    is_activated: false,
  },
];

const stats: TeacherStudentStats[] = [
  {
    id: "11111111-1111-1111-1111-111111111111",
    email: "student-a",
    display_name: "Аня",
    total_points: 120,
    week_points: 40,
    streak: 2,
    tasks_solved: 8,
    total_minutes: 45,
    last_active_date: "2026-06-18",
  },
];

const templates: HomeworkTemplate[] = [
  {
    id: "22222222-2222-2222-2222-222222222222",
    teacher_id: "t1",
    title: "Алканы",
    description: null,
    items: [{ kind: "lecture", topic: "Алканы" }],
    created_at: "2026-06-01T10:00:00Z",
    updated_at: "2026-06-01T10:00:00Z",
  },
];

const homeworkRows: HomeworkAssignment[] = [
  {
    id: "h-open",
    student_id: students[0].id,
    student_email: "student-a",
    title: "Открытое ДЗ",
    description: null,
    due_at: "2026-07-01T12:00:00Z",
    items: [],
    status: "in_progress",
    created_at: "2026-06-20T10:00:00Z",
    submission: null,
    progress: [],
    active_test_session_id: null,
  },
  {
    id: "h-cancelled",
    student_id: students[0].id,
    student_email: "student-a",
    title: "Отозванное ДЗ",
    description: null,
    due_at: null,
    items: [],
    status: "cancelled",
    created_at: "2026-06-19T10:00:00Z",
    submission: null,
    progress: [],
    active_test_session_id: null,
  },
  {
    id: "h-other",
    student_id: "99999999-9999-9999-9999-999999999999",
    student_email: "other",
    title: "Чужое ДЗ",
    description: null,
    due_at: null,
    items: [],
    status: "assigned",
    created_at: "2026-06-19T10:00:00Z",
    submission: null,
    progress: [],
    active_test_session_id: null,
  },
];

beforeEach(() => {
  vi.clearAllMocks();
  mockedListHomework.mockResolvedValue(homeworkRows);
});

describe("StudentList", () => {
  it("renders gamification columns when stats are provided", () => {
    render(<StudentList students={students} stats={stats} />);

    expect(screen.getByRole("button", { name: "student-a" })).toBeInTheDocument();
    expect(screen.queryByText("Аня")).not.toBeInTheDocument();
    expect(screen.queryByText(/Ученик-/)).not.toBeInTheDocument();
    expect(screen.getByText("40")).toBeInTheDocument();
    expect(screen.getByText("/ 120")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
    expect(screen.getByText("45 мин")).toBeInTheDocument();
    expect(screen.getByText("Баллы (нед.)")).toBeInTheDocument();
  });

  it("falls back to created date when stats are omitted", () => {
    render(<StudentList students={students} />);

    expect(screen.getByRole("button", { name: "student-a" })).toBeInTheDocument();
    expect(screen.getByText("Создан")).toBeInTheDocument();
    expect(screen.queryByText("Баллы (нед.)")).not.toBeInTheDocument();
  });

  it("shows empty state when there are no students", () => {
    render(<StudentList students={[]} stats={[]} />);

    expect(
      screen.getByText("Пока нет учеников. Создайте первого."),
    ).toBeInTheDocument();
  });

  it("opens the same sheet from (i) and login; no accordion region", async () => {
    const user = userEvent.setup();
    render(<StudentList students={students} templates={templates} />);

    const info = screen.getByRole("button", {
      name: "Информация об ученике student-a",
    });
    await user.click(info);

    const dialog = screen.getByRole("dialog", { name: "student-a" });
    expect(dialog).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: /Действия/ })).not.toBeInTheDocument();
    expect(mockedListHomework).toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Закрыть" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "student-a" }));
    expect(screen.getByRole("dialog", { name: "student-a" })).toBeInTheDocument();
  });

  it("does not open sheet when clicking track cell content", async () => {
    const user = userEvent.setup();
    render(<StudentList students={students} stats={stats} templates={templates} />);

    await user.click(screen.getByText("ЕГЭ"));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("assigns a template to the student", async () => {
    const user = userEvent.setup();
    mockedAssign.mockResolvedValue([]);

    render(<StudentList students={students} templates={templates} />);
    await user.click(screen.getByRole("button", { name: "student-a" }));
    await user.selectOptions(screen.getByLabelText("Шаблон"), templates[0].id);
    await user.click(screen.getByRole("button", { name: "Назначить" }));

    expect(mockedAssign).toHaveBeenCalledWith(templates[0].id, {
      student_id: students[0].id,
      due_at: null,
    });
    const status = await screen.findByRole("status");
    expect(status).toHaveTextContent("Назначено: «Алканы»");
    expect(screen.getByLabelText("Шаблон")).toHaveValue("");
    expect(screen.getByRole("button", { name: "Назначить" })).toBeDisabled();
    expect(refresh).toHaveBeenCalled();
    expect(mockedListHomework.mock.calls.length).toBeGreaterThanOrEqual(2);

    await user.click(screen.getByRole("button", { name: "Скрыть уведомление" }));
    expect(screen.queryByText(/Назначено: «Алканы»/)).not.toBeInTheDocument();
  });

  it("clears assign success when sheet is closed and reopened", async () => {
    const user = userEvent.setup();
    mockedAssign.mockResolvedValue([]);

    render(<StudentList students={students} templates={templates} />);
    await user.click(screen.getByRole("button", { name: "student-a" }));
    await user.selectOptions(screen.getByLabelText("Шаблон"), templates[0].id);
    await user.click(screen.getByRole("button", { name: "Назначить" }));
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Назначено: «Алканы»",
    );

    await user.click(screen.getByRole("button", { name: "Закрыть" }));
    await user.click(screen.getByRole("button", { name: "student-a" }));
    expect(screen.queryByText(/Назначено: «Алканы»/)).not.toBeInTheDocument();
  });

  it("shows homework history with cancelled label and open section", async () => {
    const user = userEvent.setup();
    render(<StudentList students={students} templates={templates} />);
    await user.click(screen.getByRole("button", { name: "student-a" }));

    const dialog = await screen.findByRole("dialog", { name: "student-a" });
    expect(within(dialog).getAllByText("Открытое ДЗ").length).toBeGreaterThanOrEqual(1);
    expect(within(dialog).getByText("Отозванное ДЗ")).toBeInTheDocument();
    expect(within(dialog).getByText("Отменено")).toBeInTheDocument();
    expect(within(dialog).queryByText("Чужое ДЗ")).not.toBeInTheDocument();
    expect(within(dialog).getByRole("heading", { name: "Открытые" })).toBeInTheDocument();
  });

  it("shows AI placeholder without tutor API usage", async () => {
    const user = userEvent.setup();
    render(<StudentList students={students} templates={templates} />);
    await user.click(screen.getByRole("button", { name: "student-a" }));

    const dialog = await screen.findByRole("dialog", { name: "student-a" });
    expect(
      within(dialog).getByRole("heading", { name: "Диалоги AI" }),
    ).toBeInTheDocument();
    expect(within(dialog).getByText("Скоро")).toBeInTheDocument();
  });

  it("shows temporary password after reset", async () => {
    const user = userEvent.setup();
    mockedReset.mockResolvedValue({ temporary_password: "tmp-secret" });

    render(<StudentList students={students} templates={templates} />);
    await user.click(screen.getByRole("button", { name: "student-a" }));
    await user.click(screen.getByRole("button", { name: "Сбросить пароль" }));

    expect(mockedReset).toHaveBeenCalledWith(students[0].id);
    const status = await screen.findByRole("status");
    expect(status).toHaveTextContent("Новый временный пароль");
    expect(within(status).getByText("tmp-secret")).toBeInTheDocument();
  });

  it("deletes a student after confirm and closes sheet", async () => {
    const user = userEvent.setup();
    mockedDelete.mockResolvedValue(undefined);
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<StudentList students={students} templates={templates} />);
    await user.click(screen.getByRole("button", { name: "student-a" }));
    await user.click(screen.getByRole("button", { name: "Удалить ученика" }));

    expect(window.confirm).toHaveBeenCalled();
    expect(mockedDelete).toHaveBeenCalledWith(students[0].id);
    expect(refresh).toHaveBeenCalled();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
