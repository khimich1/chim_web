import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { HomeworkForm } from "@/components/homework/HomeworkForm";
import { createHomework } from "@/lib/api/homework";

const push = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh }),
}));

vi.mock("@/lib/api/homework", () => ({
  createHomework: vi.fn(),
}));

const mockedCreate = vi.mocked(createHomework);

const students = [
  {
    id: "student-1",
    email: "student@example.com",
    track: "ege" as const,
    created_at: "2026-01-01T00:00:00Z",
  },
];

const topics = ["Алканы", "Соли"];
const variantsByTrack = {
  ege: ["003.txt", "007.txt"],
  oge: ["001.txt"],
};

beforeEach(() => {
  vi.clearAllMocks();
  mockedCreate.mockResolvedValue({
    id: "hw-1",
    student_id: "student-1",
    student_email: null,
    title: "ДЗ",
    description: null,
    due_at: null,
    items: [],
    status: "assigned",
    created_at: "2026-01-01T00:00:00Z",
    submission: null,
    progress: [],
  });
});

async function fillTitle(title: string) {
  await userEvent.type(screen.getByLabelText("Название"), title);
}

describe("HomeworkForm", () => {
  it("adds and removes multiple items from different variants", async () => {
    render(
      <HomeworkForm
        students={students}
        topics={topics}
        variantsByTrack={variantsByTrack}
      />,
    );

    await fillTitle("Смешанное ДЗ");

    await userEvent.selectOptions(screen.getByLabelText("Тип пункта"), "lecture");
    await userEvent.selectOptions(screen.getByLabelText("Тема"), "Алканы");
    await userEvent.click(screen.getByRole("button", { name: "Добавить пункт" }));

    await userEvent.selectOptions(
      screen.getByLabelText("Тип пункта"),
      "test_partial",
    );
    await userEvent.selectOptions(screen.getByLabelText("Вариант"), "003.txt");
    await userEvent.click(screen.getByRole("button", { name: "11" }));
    await userEvent.click(screen.getByRole("button", { name: "Добавить пункт" }));

    await userEvent.selectOptions(screen.getByLabelText("Вариант"), "007.txt");
    await userEvent.click(screen.getByRole("button", { name: "10" }));
    await userEvent.click(screen.getByRole("button", { name: "15" }));
    await userEvent.click(screen.getByRole("button", { name: "Добавить пункт" }));

    expect(screen.getByText(/1\. Лекция: Алканы/)).toBeInTheDocument();
    expect(
      screen.getByText(/2\. Тест: 003, задания 10/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/3\. Тест: 007, задания 15/),
    ).toBeInTheDocument();

    await userEvent.click(screen.getAllByRole("button", { name: "Удалить" })[1]);
    expect(screen.queryByText(/2\. Тест: 003/)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Назначить" }));

    expect(mockedCreate).toHaveBeenCalledWith({
      student_id: "student-1",
      title: "Смешанное ДЗ",
      description: null,
      items: [
        { kind: "lecture", topic: "Алканы" },
        { kind: "test_partial", variant: "007.txt", types: [15] },
      ],
    });
    expect(push).toHaveBeenCalledWith("/teacher/homework");
  });

  it("blocks submit when no items were added", async () => {
    render(
      <HomeworkForm
        students={students}
        topics={topics}
        variantsByTrack={variantsByTrack}
      />,
    );

    await fillTitle("Пустое ДЗ");

    expect(screen.getByRole("button", { name: "Назначить" })).toBeDisabled();
    expect(mockedCreate).not.toHaveBeenCalled();
  });

  it("adds test_by_type without variant picker", async () => {
    render(
      <HomeworkForm
        students={students}
        topics={topics}
        variantsByTrack={variantsByTrack}
      />,
    );

    await fillTitle("Все десятые");

    await userEvent.selectOptions(
      screen.getByLabelText("Тип пункта"),
      "test_by_type",
    );
    expect(screen.queryByLabelText("Вариант")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "11" }));
    await userEvent.click(screen.getByRole("button", { name: "Добавить пункт" }));

    expect(
      screen.getByText(/1\. Тест: №10 по всем вариантам/),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Назначить" }));

    expect(mockedCreate).toHaveBeenCalledWith({
      student_id: "student-1",
      title: "Все десятые",
      description: null,
      items: [{ kind: "test_by_type", types: [10] }],
    });
  });

  it("shows OGE type range for an OGE student", async () => {
    render(
      <HomeworkForm
        students={[
          {
            id: "student-oge",
            email: "oge@example.com",
            track: "oge",
            created_at: "2026-01-01T00:00:00Z",
          },
        ]}
        topics={topics}
        variantsByTrack={variantsByTrack}
      />,
    );

    await userEvent.selectOptions(
      screen.getByLabelText("Тип пункта"),
      "test_partial",
    );

    expect(screen.getByRole("button", { name: "19" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "28" })).not.toBeInTheDocument();
  });
});
