import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { GroupsPanel } from "@/components/students/GroupsPanel";
import {
  createTeacherGroup,
  getTeacherGroup,
  listTeacherGroups,
  renameTeacherGroup,
  replaceTeacherGroupMembers,
} from "@/lib/api/groups";
import { assignHomeworkTemplate } from "@/lib/api/templates";
import type { HomeworkTemplate, Student } from "@/lib/api/types";

vi.mock("@/lib/api/groups", () => ({
  listTeacherGroups: vi.fn(),
  getTeacherGroup: vi.fn(),
  createTeacherGroup: vi.fn(),
  renameTeacherGroup: vi.fn(),
  deleteTeacherGroup: vi.fn(),
  replaceTeacherGroupMembers: vi.fn(),
}));

vi.mock("@/lib/api/templates", () => ({
  assignHomeworkTemplate: vi.fn(),
}));

const mockedList = vi.mocked(listTeacherGroups);
const mockedGet = vi.mocked(getTeacherGroup);
const mockedCreate = vi.mocked(createTeacherGroup);
const mockedRename = vi.mocked(renameTeacherGroup);
const mockedReplace = vi.mocked(replaceTeacherGroupMembers);
const mockedAssign = vi.mocked(assignHomeworkTemplate);

const students: Student[] = [
  {
    id: "s1",
    email: "anna",
    track: "ege",
    created_at: "2026-06-01T10:00:00Z",
    first_login_at: null,
    onboarding_completed_at: null,
    is_activated: true,
  },
  {
    id: "s2",
    email: "boris",
    track: "ege",
    created_at: "2026-06-01T10:00:00Z",
    first_login_at: null,
    onboarding_completed_at: null,
    is_activated: true,
  },
  {
    id: "s3",
    email: "clara",
    track: "oge",
    created_at: "2026-06-01T10:00:00Z",
    first_login_at: null,
    onboarding_completed_at: null,
    is_activated: true,
  },
];

const templates: HomeworkTemplate[] = [
  {
    id: "t1",
    teacher_id: "teacher",
    title: "Алканы",
    description: null,
    items: [{ kind: "lecture", topic: "Алканы" }],
    created_at: "2026-06-01T10:00:00Z",
    updated_at: "2026-06-01T10:00:00Z",
  },
];

const emptyGroup = {
  id: "g1",
  teacher_id: "teacher",
  name: "Группа 1",
  member_count: 0,
  created_at: "2026-06-01T10:00:00Z",
  members: [],
};

beforeEach(() => {
  vi.clearAllMocks();
  mockedList.mockResolvedValue([]);
  mockedGet.mockResolvedValue(emptyGroup);
});

describe("GroupsPanel", () => {
  it("creates a group with default name Группа N", async () => {
    const user = userEvent.setup();
    mockedCreate.mockResolvedValue(emptyGroup);
    mockedList
      .mockResolvedValueOnce([])
      .mockResolvedValue([{ ...emptyGroup, members: undefined } as never]);
    // After create, refresh loads the new group
    mockedList.mockResolvedValue([
      {
        id: "g1",
        teacher_id: "teacher",
        name: "Группа 1",
        member_count: 0,
        created_at: "2026-06-01T10:00:00Z",
      },
    ]);
    mockedGet.mockResolvedValue(emptyGroup);

    render(<GroupsPanel students={students} templates={templates} />);

    await screen.findByText(/Групп пока нет/);
    await user.click(screen.getByRole("button", { name: "Создать группу" }));

    expect(mockedCreate).toHaveBeenCalledWith({});
    expect(await screen.findByText("Группа 1")).toBeInTheDocument();
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Создана группа «Группа 1»",
    );
  });

  it("does not offer students already in another group", async () => {
    const user = userEvent.setup();
    const groupA = {
      id: "g1",
      teacher_id: "teacher",
      name: "Группа 1",
      member_count: 0,
      created_at: "2026-06-01T10:00:00Z",
      members: [],
    };
    const groupB = {
      id: "g2",
      teacher_id: "teacher",
      name: "Группа 2",
      member_count: 1,
      created_at: "2026-06-01T10:00:00Z",
      members: [{ id: "s2", email: "boris", track: "ege" as const }],
    };

    mockedList.mockResolvedValue([
      {
        id: "g1",
        teacher_id: "teacher",
        name: "Группа 1",
        member_count: 0,
        created_at: "2026-06-01T10:00:00Z",
      },
      {
        id: "g2",
        teacher_id: "teacher",
        name: "Группа 2",
        member_count: 1,
        created_at: "2026-06-01T10:00:00Z",
      },
    ]);
    mockedGet.mockImplementation(async (id: string) =>
      id === "g1" ? groupA : groupB,
    );

    render(<GroupsPanel students={students} templates={templates} />);

    await screen.findByRole("button", { name: /Группа 1/ });
    const panel = await screen.findByRole("region", { name: /Группа Группа 1/ });
    expect(within(panel).getByText(/anna/)).toBeInTheDocument();
    expect(within(panel).getByText(/clara/)).toBeInTheDocument();
    expect(within(panel).queryByLabelText(/boris/)).not.toBeInTheDocument();
    expect(within(panel).getByText(/boris → Группа 2/)).toBeInTheDocument();

    // smoke: rename still works
    await user.clear(within(panel).getByLabelText("Название"));
    await user.type(within(panel).getByLabelText("Название"), "Утренние");
    mockedRename.mockResolvedValue({ ...groupA, name: "Утренние" });
    mockedList.mockResolvedValue([
      {
        id: "g1",
        teacher_id: "teacher",
        name: "Утренние",
        member_count: 0,
        created_at: "2026-06-01T10:00:00Z",
      },
      {
        id: "g2",
        teacher_id: "teacher",
        name: "Группа 2",
        member_count: 1,
        created_at: "2026-06-01T10:00:00Z",
      },
    ]);
    await user.click(within(panel).getByRole("button", { name: "Сохранить имя" }));
    await waitFor(() =>
      expect(mockedRename).toHaveBeenCalledWith("g1", "Утренние"),
    );
  });

  it("saves members and assigns template to non-empty group", async () => {
    const user = userEvent.setup();
    const empty = { ...emptyGroup };
    const withMembers = {
      ...emptyGroup,
      member_count: 2,
      members: [
        { id: "s1", email: "anna", track: "ege" as const },
        { id: "s3", email: "clara", track: "oge" as const },
      ],
    };

    mockedList.mockResolvedValue([
      {
        id: "g1",
        teacher_id: "teacher",
        name: "Группа 1",
        member_count: 0,
        created_at: "2026-06-01T10:00:00Z",
      },
    ]);
    mockedGet.mockResolvedValue(empty);

    render(<GroupsPanel students={students} templates={templates} />);

    const panel = await screen.findByRole("region", { name: /Группа Группа 1/ });
    await user.click(within(panel).getByLabelText(/anna/));
    await user.click(within(panel).getByLabelText(/clara/));

    mockedReplace.mockResolvedValue(withMembers);
    mockedList.mockResolvedValue([
      {
        id: "g1",
        teacher_id: "teacher",
        name: "Группа 1",
        member_count: 2,
        created_at: "2026-06-01T10:00:00Z",
      },
    ]);
    mockedGet.mockResolvedValue(withMembers);

    await user.click(
      within(panel).getByRole("button", { name: "Сохранить состав" }),
    );
    expect(mockedReplace).toHaveBeenCalledWith("g1", ["s1", "s3"]);

    await waitFor(() =>
      expect(screen.getByLabelText("Шаблон")).toBeEnabled(),
    );

    await user.selectOptions(screen.getByLabelText("Шаблон"), "t1");
    mockedAssign.mockResolvedValue([
      { id: "h1" } as never,
      { id: "h2" } as never,
    ]);
    await user.click(screen.getByRole("button", { name: "Назначить группе" }));

    expect(mockedAssign).toHaveBeenCalledWith("t1", { group_id: "g1" });
    const status = await screen.findByRole("status");
    expect(status).toHaveTextContent(
      "Назначено: «Алканы» — назначено ученикам: 2",
    );
    expect(screen.getByLabelText("Шаблон")).toHaveValue("");
    expect(
      screen.getByRole("button", { name: "Назначить группе" }),
    ).toBeDisabled();

    await user.click(
      screen.getByRole("button", { name: "Скрыть уведомление" }),
    );
    expect(screen.queryByText(/Назначено: «Алканы»/)).not.toBeInTheDocument();
  });
});
