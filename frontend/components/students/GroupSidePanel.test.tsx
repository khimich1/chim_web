import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { GroupSidePanel } from "@/components/students/GroupSidePanel";
import type { StudentGroupDetail } from "@/lib/api/groups";
import {
  cancelHomework,
  listHomework,
  restoreHomework,
} from "@/lib/api/homework";
import { assignHomeworkTemplate } from "@/lib/api/templates";
import type { HomeworkAssignment, HomeworkTemplate, Student } from "@/lib/api/types";

vi.mock("@/lib/api/groups", () => ({
  renameTeacherGroup: vi.fn(),
  replaceTeacherGroupMembers: vi.fn(),
  deleteTeacherGroup: vi.fn(),
}));

vi.mock("@/lib/api/homework", () => ({
  listHomework: vi.fn(),
  cancelHomework: vi.fn(),
  restoreHomework: vi.fn(),
}));

vi.mock("@/lib/api/templates", () => ({
  assignHomeworkTemplate: vi.fn(),
}));

const mockedList = vi.mocked(listHomework);
const mockedCancel = vi.mocked(cancelHomework);
const mockedRestore = vi.mocked(restoreHomework);
const mockedAssign = vi.mocked(assignHomeworkTemplate);

const group: StudentGroupDetail = {
  id: "g1",
  name: "Группа 1",
  teacher_id: "t1",
  created_at: "2026-06-01T10:00:00Z",
  member_count: 2,
  members: [
    {
      id: "s1",
      email: "anna",
      track: "ege",
    },
    {
      id: "s2",
      email: "boris",
      track: "ege",
    },
  ],
};

const students: Student[] = group.members;

const templates: HomeworkTemplate[] = [
  {
    id: "t1",
    teacher_id: "t1",
    title: "Алканы",
    description: null,
    items: [{ kind: "lecture", topic: "Алканы" }],
    created_at: "2026-06-01T10:00:00Z",
    updated_at: "2026-06-01T10:00:00Z",
  },
];

function waveRows(overrides?: Partial<HomeworkAssignment>): HomeworkAssignment[] {
  const base = {
    student_email: null,
    description: null,
    due_at: null,
    items: [] as HomeworkAssignment["items"],
    status: "assigned" as const,
    created_at: "2026-06-20T10:00:00Z",
    template_id: "t1",
    source_group_id: "g1",
    assign_batch_id: "batch-1",
    cancelled_at: null,
    submission: null,
    progress: [],
    active_test_session_id: null,
    ...overrides,
  };
  return [
    {
      ...base,
      id: "h1",
      student_id: "s1",
      title: "Алканы",
    },
    {
      ...base,
      id: "h2",
      student_id: "s2",
      title: "Алканы",
    },
  ];
}

beforeEach(() => {
  vi.clearAllMocks();
  mockedList.mockResolvedValue(waveRows());
  mockedCancel.mockResolvedValue({
    cancelled_ids: ["h1", "h2"],
    skipped_submitted_count: 0,
    cancelled_at: "2026-06-20T12:00:00Z",
  });
  mockedRestore.mockResolvedValue({ restored_ids: ["h1", "h2"] });
  mockedAssign.mockResolvedValue(waveRows());
});

describe("GroupSidePanel history + revoke", () => {
  it("groups homework into one wave row and refreshes after assign", async () => {
    const user = userEvent.setup();
    render(
      <GroupSidePanel
        group={group}
        students={students}
        templates={templates}
        membershipByStudent={new Map()}
        open
        onClose={vi.fn()}
        onUpdated={vi.fn()}
        onDeleted={vi.fn()}
      />,
    );

    expect(await screen.findByText("Алканы")).toBeInTheDocument();
    expect(screen.getByText(/2 уч\./)).toBeInTheDocument();
    const history = screen.getByRole("list", { name: "История раздач" });
    expect(history.querySelectorAll("li")).toHaveLength(1);

    await user.selectOptions(
      screen.getByLabelText("Шаблон"),
      "t1",
    );
    await user.click(screen.getByRole("button", { name: "Назначить группе" }));
    await waitFor(() => {
      expect(mockedAssign).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(mockedList.mock.calls.length).toBeGreaterThan(1);
    });
  });

  it("cancels wave and restores via undo", async () => {
    const user = userEvent.setup();
    render(
      <GroupSidePanel
        group={group}
        students={students}
        templates={templates}
        membershipByStudent={new Map()}
        open
        onClose={vi.fn()}
        onUpdated={vi.fn()}
        onDeleted={vi.fn()}
      />,
    );

    const trash = await screen.findByRole("button", {
      name: 'Отозвать задание «Алканы»',
    });
    await user.click(trash);
    await waitFor(() => {
      expect(mockedCancel).toHaveBeenCalledWith("h1", "wave");
    });
    expect(await screen.findByText(/Отозвано: «Алканы»/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Вернуть" }));
    await waitFor(() => {
      expect(mockedRestore).toHaveBeenCalledWith("h1", "wave");
    });
  });
});
