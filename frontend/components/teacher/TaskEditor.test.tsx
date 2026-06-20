import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TaskEditor } from "@/components/teacher/TaskEditor";
import { createThemeTask } from "@/lib/api/teacher-themes";

vi.mock("@/components/teacher/ContentBlocksEditor", () => ({
  ContentBlocksEditor: ({
    label,
    onChange,
  }: {
    label: string;
    onChange: (blocks: { type: string; content?: string }[]) => void;
  }) => (
    <div>
      <span>{label}</span>
      <button
        type="button"
        onClick={() => onChange([{ type: "text", content: "Вопрос?" }])}
      >
        Fill {label}
      </button>
    </div>
  ),
}));

vi.mock("@/lib/api/teacher-themes", () => ({
  createThemeTask: vi.fn(),
  updateThemeTask: vi.fn(),
  deleteThemeTask: vi.fn(),
}));

const mockedCreate = vi.mocked(createThemeTask);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("TaskEditor", () => {
  it("creates auto-graded task with correct_value", async () => {
    const onSaved = vi.fn();
    mockedCreate.mockResolvedValue({
      id: "task-1",
      theme_id: "theme-1",
      title: null,
      sort_order: 0,
      grading_mode: "auto",
      question_blocks: [{ type: "text", content: "Вопрос?" }],
      reference_answer: null,
      correct_value: "42",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    render(<TaskEditor themeId="theme-1" onSaved={onSaved} />);

    await userEvent.click(screen.getByRole("button", { name: "Fill Вопрос" }));
    await userEvent.type(screen.getByLabelText("Правильный ответ"), "42");
    await userEvent.click(
      screen.getByRole("button", { name: "Сохранить задание" }),
    );

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith("theme-1", {
        title: null,
        grading_mode: "auto",
        question_blocks: [{ type: "text", content: "Вопрос?" }],
        correct_value: "42",
        reference_answer: null,
      });
    });
    expect(onSaved).toHaveBeenCalled();
  });

  it("requires reference answer for self_check", async () => {
    render(<TaskEditor themeId="theme-1" onSaved={vi.fn()} />);

    await userEvent.click(
      screen.getByLabelText(/Самопроверка/i),
    );
    await userEvent.click(screen.getByRole("button", { name: "Fill Вопрос" }));
    await userEvent.click(
      screen.getByRole("button", { name: "Сохранить задание" }),
    );

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent("эталонный ответ");
    expect(mockedCreate).not.toHaveBeenCalled();
  });
});
