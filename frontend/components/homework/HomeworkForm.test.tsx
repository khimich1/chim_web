import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { HomeworkForm } from "@/components/homework/HomeworkForm";
import { createHomeworkTemplate } from "@/lib/api/templates";

const push = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh }),
}));

vi.mock("@/lib/api/templates", () => ({
  createHomeworkTemplate: vi.fn(),
  updateHomeworkTemplate: vi.fn(),
}));

const mockedCreate = vi.mocked(createHomeworkTemplate);

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
    id: "tpl-1",
    teacher_id: "teacher-1",
    title: "ДЗ",
    description: null,
    items: [],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  });
});

function fillTitle(title: string) {
  fireEvent.change(screen.getByLabelText("Название"), {
    target: { value: title },
  });
}

function renderForm() {
  return render(
    <HomeworkForm
      topics={topics}
      variantsByTrack={variantsByTrack}
      teacherThemes={teacherThemes}
    />,
  );
}

describe("HomeworkForm", () => {
  it("has no student select field", () => {
    renderForm();
    expect(screen.queryByLabelText("Ученик")).not.toBeInTheDocument();
    expect(
      screen.getByLabelText("Контент для тестовых пунктов"),
    ).toBeInTheDocument();
  });

  it(
    "adds and removes multiple items from different variants",
    async () => {
      const user = userEvent.setup();
      renderForm();

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

      await user.click(screen.getByRole("button", { name: "Создать шаблон" }));

      await waitFor(() => {
        expect(mockedCreate).toHaveBeenCalledWith({
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
    renderForm();
    await fillTitle("Пустое ДЗ");

    expect(
      screen.getByRole("button", { name: "Создать шаблон" }),
    ).toBeDisabled();
    expect(mockedCreate).not.toHaveBeenCalled();
  });

  it("adds test_by_type without variant picker", async () => {
    renderForm();
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

    await userEvent.click(screen.getByRole("button", { name: "Создать шаблон" }));

    expect(mockedCreate).toHaveBeenCalledWith({
      title: "Все десятые",
      description: null,
      items: [{ kind: "test_by_type", types: [10] }],
    });
  });

  it("shows EGE type range including written tasks 29–34", async () => {
    renderForm();

    await userEvent.selectOptions(
      screen.getByLabelText("Тип пункта"),
      "test_partial",
    );

    expect(screen.getByRole("button", { name: "29" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "34" })).toBeInTheDocument();
  });

  it("adds test_by_type with EGE written task numbers", async () => {
    renderForm();
    await fillTitle("Письменная часть");

    await userEvent.selectOptions(
      screen.getByLabelText("Тип пункта"),
      "test_by_type",
    );
    await userEvent.click(screen.getByRole("button", { name: "10" }));
    await userEvent.click(screen.getByRole("button", { name: "11" }));
    await userEvent.click(screen.getByRole("button", { name: "29" }));
    await userEvent.click(screen.getByRole("button", { name: "30" }));
    await userEvent.click(screen.getByRole("button", { name: "Добавить пункт" }));

    expect(screen.getByText(/1\. Тест: №29, 30 по вариантам/)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Создать шаблон" }));

    expect(mockedCreate).toHaveBeenCalledWith({
      title: "Письменная часть",
      description: null,
      items: [{ kind: "test_by_type", types: [29, 30] }],
    });
  });

  it("shows OGE type range when content track is OGE", async () => {
    renderForm();

    await userEvent.selectOptions(
      screen.getByLabelText("Контент для тестовых пунктов"),
      "oge",
    );
    await userEvent.selectOptions(
      screen.getByLabelText("Тип пункта"),
      "test_partial",
    );

    expect(screen.getByRole("button", { name: "19" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "28" })).not.toBeInTheDocument();
  });

  it("adds custom_theme with optional task selection", async () => {
    renderForm();
    await fillTitle("Кастомная тема");

    await userEvent.selectOptions(
      screen.getByLabelText("Тип пункта"),
      "custom_theme",
    );
    await userEvent.click(screen.getByRole("checkbox", { name: /Auto task/i }));
    await userEvent.click(screen.getByRole("button", { name: "Добавить пункт" }));

    expect(screen.getByText(/1\. Тема: ОВР \(1 зад\.\)/)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Создать шаблон" }));

    expect(mockedCreate).toHaveBeenCalledWith({
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
    renderForm();
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

    await userEvent.click(screen.getByRole("button", { name: "Создать шаблон" }));

    expect(mockedCreate).toHaveBeenCalledWith({
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
