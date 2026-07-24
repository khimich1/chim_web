import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { GroupsPanel } from "@/components/students/GroupsPanel";
import {
  createTeacherGroup,
  deleteTeacherGroup,
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

vi.mock("@/lib/api/homework", () => ({
  listHomework: vi.fn().mockResolvedValue([]),
  cancelHomework: vi.fn(),
  restoreHomework: vi.fn(),
}));

const mockedList = vi.mocked(listTeacherGroups);
const mockedGet = vi.mocked(getTeacherGroup);
const mockedCreate = vi.mocked(createTeacherGroup);
const mockedRename = vi.mocked(renameTeacherGroup);
const mockedReplace = vi.mocked(replaceTeacherGroupMembers);
const mockedAssign = vi.mocked(assignHomeworkTemplate);
const mockedDelete = vi.mocked(deleteTeacherGroup);

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

async function openGroupSheet(user: ReturnType<typeof userEvent.setup>, name = /Группа 1/) {
  await user.click(await screen.findByRole("button", { name }));
  return screen.findByRole("dialog", { name: /Группа/ });
}

describe("GroupsPanel", () => {
  it("stays list-only until a group is opened", async () => {
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

    expect(await screen.findByRole("button", { name: /Группа 1/ })).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: /Группа/ })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("В группе")).not.toBeInTheDocument();
  });

  it("creates a group and opens its sheet", async () => {
    const user = userEvent.setup();
    mockedCreate.mockResolvedValue(emptyGroup);
    mockedList
      .mockResolvedValueOnce([])
      .mockResolvedValue([
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
    expect(await screen.findByRole("dialog", { name: "Группа 1" })).toBeInTheDocument();
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Создана группа «Группа 1»",
    );
  });

  it("does not offer students already in another group in free list", async () => {
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

    const dialog = await openGroupSheet(user, /Группа 1/);
    const free = within(dialog).getByLabelText("Свободные");
    expect(within(free).getByText(/anna/)).toBeInTheDocument();
    expect(within(free).getByText(/clara/)).toBeInTheDocument();
    expect(within(free).queryByText(/boris/)).not.toBeInTheDocument();
    expect(within(dialog).getByText(/boris → Группа 2/)).toBeInTheDocument();

    await user.clear(within(dialog).getByLabelText("Название"));
    await user.type(within(dialog).getByLabelText("Название"), "Утренние");
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
    await user.click(within(dialog).getByRole("button", { name: "Сохранить имя" }));
    await waitFor(() =>
      expect(mockedRename).toHaveBeenCalledWith("g1", "Утренние"),
    );
  });

  it("saves dual-list members and assigns template to non-empty group", async () => {
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

    const dialog = await openGroupSheet(user);
    const free = within(dialog).getByLabelText("Свободные");

    await user.click(within(free).getByRole("button", { name: /anna/ }));
    await user.click(
      within(dialog).getByRole("button", { name: "Добавить в группу" }),
    );
    await user.click(within(free).getByRole("button", { name: /clara/ }));
    await user.click(
      within(dialog).getByRole("button", { name: "Добавить в группу" }),
    );

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
      within(dialog).getByRole("button", { name: "Сохранить состав" }),
    );
    expect(mockedReplace).toHaveBeenCalledWith("g1", ["s1", "s3"]);

    await waitFor(() =>
      expect(within(dialog).getByLabelText("Шаблон")).toBeEnabled(),
    );

    await user.selectOptions(within(dialog).getByLabelText("Шаблон"), "t1");
    mockedAssign.mockResolvedValue([
      { id: "h1" } as never,
      { id: "h2" } as never,
    ]);
    await user.click(
      within(dialog).getByRole("button", { name: "Назначить группе" }),
    );

    expect(mockedAssign).toHaveBeenCalledWith("t1", { group_id: "g1" });
    const status = await within(dialog).findByRole("status");
    expect(status).toHaveTextContent(
      "Назначено: «Алканы» — назначено ученикам: 2",
    );
    expect(within(dialog).getByLabelText("Шаблон")).toHaveValue("");
    expect(
      within(dialog).getByRole("button", { name: "Назначить группе" }),
    ).toBeDisabled();

    await user.click(
      within(dialog).getByRole("button", { name: "Скрыть уведомление" }),
    );
    expect(
      within(dialog).queryByText(/Назначено: «Алканы»/),
    ).not.toBeInTheDocument();
  });

  it("deletes a group and closes the sheet", async () => {
    const user = userEvent.setup();
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
    mockedDelete.mockResolvedValue(undefined);
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<GroupsPanel students={students} templates={templates} />);
    const dialog = await openGroupSheet(user);

    mockedList.mockResolvedValue([]);
    await user.click(
      within(dialog).getByRole("button", { name: "Удалить группу" }),
    );

    expect(mockedDelete).toHaveBeenCalledWith("g1");
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    expect(await screen.findByText(/Групп пока нет/)).toBeInTheDocument();
  });
});
