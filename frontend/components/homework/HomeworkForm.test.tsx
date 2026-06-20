import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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

const teacherThemes = [
  {
    id: "theme-1",
    title: "ОВР",
    tasks: [
      {
        id: "task-auto",
        theme_id: "theme-1",
        title: "Auto task",
        sort_order: 0,
        grading_mode: "auto" as const,
        question_blocks: [{ type: "text" as const, content: "Q" }],
        reference_answer: null,
        correct_value: "4",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
      {
        id: "task-self",
        theme_id: "theme-1",
        title: "Self check",
        sort_order: 1,
        grading_mode: "self_check" as const,
        question_blocks: [{ type: "text" as const, content: "Q2" }],
        reference_answer: [{ type: "text" as const, content: "Ref" }],
        correct_value: null,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
    ],
  },
];

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

function fillTitle(title: string) {
  fireEvent.change(screen.getByLabelText("Название"), {
    target: { value: title },
  });
}

describe("HomeworkForm", () => {
  it(
    "adds and removes multiple items from different variants",
    async () => {
      const user = userEvent.setup();

      render(
        <HomeworkForm
          students={students}
          topics={topics}
          variantsByTrack={variantsByTrack}
          teacherThemes={teacherThemes}
        />,
      );

      fillTitle("Смешанное ДЗ");

      await user.selectOptions(
        screen.getByLabelText("Тип пункта"),
        "lecture",
      );
      await user.selectOptions(screen.getByLabelText("Тема"), "Алканы");
      await user.click(screen.getByRole("button", { name: "Добавить пункт" }));

      await user.selectOptions(
        screen.getByLabelText("Тип пункта"),
        "test_partial",
      );
      await user.selectOptions(screen.getByLabelText("Вариант"), "003.txt");
      await user.click(screen.getByRole("button", { name: "11" }));
      await user.click(screen.getByRole("button", { name: "Добавить пункт" }));

      await user.selectOptions(screen.getByLabelText("Вариант"), "007.txt");
      await user.click(screen.getByRole("button", { name: "10" }));
      await user.click(screen.getByRole("button", { name: "15" }));
      await user.click(screen.getByRole("button", { name: "Добавить пункт" }));

      await waitFor(() => {
        expect(screen.getByText(/1\. Лекция: Алканы/)).toBeInTheDocument();
        expect(
          screen.getByText(/2\. Тест: 003, задания 10/),
        ).toBeInTheDocument();
        expect(
          screen.getByText(/3\. Тест: 007, задания 15/),
        ).toBeInTheDocument();
      });

      await user.click(
        screen.getAllByRole("button", { name: "Удалить" })[1],
      );
      await waitFor(() => {
        expect(screen.queryByText(/2\. Тест: 003/)).not.toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: "Назначить" }));

      await waitFor(() => {
        expect(mockedCreate).toHaveBeenCalledWith({
          student_id: "student-1",
          title: "Смешанное ДЗ",
          description: null,
          items: [
            { kind: "lecture", topic: "Алканы" },
            { kind: "test_partial", variant: "007.txt", types: [15] },
          ],
        });
      });
      expect(push).toHaveBeenCalledWith("/teacher/homework");
    },
    10_000,
  );

  it("blocks submit when no items were added", async () => {
    render(
      <HomeworkForm
        students={students}
        topics={topics}
        variantsByTrack={variantsByTrack}
        teacherThemes={teacherThemes}
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
        teacherThemes={teacherThemes}
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
      screen.getByText(/1\. Тест: №10 по вариантам/),
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
        teacherThemes={teacherThemes}
      />,
    );

    await userEvent.selectOptions(
      screen.getByLabelText("Тип пункта"),
      "test_partial",
    );

    expect(screen.getByRole("button", { name: "19" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "28" })).not.toBeInTheDocument();
  });

  it("adds custom_theme with optional task selection", async () => {
    render(
      <HomeworkForm
        students={students}
        topics={topics}
        variantsByTrack={variantsByTrack}
        teacherThemes={teacherThemes}
      />,
    );

    await fillTitle("Кастомная тема");

    await userEvent.selectOptions(
      screen.getByLabelText("Тип пункта"),
      "custom_theme",
    );
    await userEvent.click(screen.getByRole("checkbox", { name: /Auto task/i }));
    await userEvent.click(screen.getByRole("button", { name: "Добавить пункт" }));

    expect(screen.getByText(/1\. Тема: ОВР \(1 зад\.\)/)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Назначить" }));

    expect(mockedCreate).toHaveBeenCalledWith({
      student_id: "student-1",
      title: "Кастомная тема",
      description: null,
      items: [
        {
          kind: "custom_theme",
          theme_id: "theme-1",
          task_ids: ["task-auto"],
        },
      ],
    });
  });

  it("adds test_by_type with selected variants", async () => {
    render(
      <HomeworkForm
        students={students}
        topics={topics}
        variantsByTrack={variantsByTrack}
        teacherThemes={teacherThemes}
      />,
    );

    await fillTitle("Выбор вариантов");

    await userEvent.selectOptions(
      screen.getByLabelText("Тип пункта"),
      "test_by_type",
    );
    await userEvent.click(screen.getByRole("button", { name: "11" }));
    await userEvent.click(screen.getByRole("button", { name: "003" }));
    await userEvent.click(screen.getByRole("button", { name: "007" }));
    await userEvent.click(screen.getByRole("button", { name: "Добавить пункт" }));

    expect(screen.getByText(/варианты: 003, 007/)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Назначить" }));

    expect(mockedCreate).toHaveBeenCalledWith({
      student_id: "student-1",
      title: "Выбор вариантов",
      description: null,
      items: [
        {
          kind: "test_by_type",
          types: [10],
          variants: ["003.txt", "007.txt"],
        },
      ],
    });
  });
});
