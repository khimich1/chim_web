import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ThemeEditor } from "@/components/teacher/ThemeEditor";
import { updateTeacherTheme } from "@/lib/api/teacher-themes";
import type { TeacherTheme } from "@/lib/api/types";

vi.mock("@/lib/api/teacher-themes", () => ({
  updateTeacherTheme: vi.fn(),
}));

const mockedUpdate = vi.mocked(updateTeacherTheme);

const theme: TeacherTheme = {
  id: "theme-1",
  teacher_id: "teacher-1",
  title: "Кислоты",
  description: "Базовая тема",
  is_published: false,
  sort_order: 0,
  task_count: 2,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ThemeEditor", () => {
  it("saves theme fields", async () => {
    const onSaved = vi.fn();
    mockedUpdate.mockResolvedValue({
      ...theme,
      title: "Кислоты и основания",
      is_published: true,
    });

    render(<ThemeEditor theme={theme} onSaved={onSaved} />);

    await userEvent.clear(screen.getByLabelText("Название"));
    await userEvent.type(screen.getByLabelText("Название"), "Кислоты и основания");
    await userEvent.click(
      screen.getByRole("checkbox", { name: /Опубликована/i }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Сохранить тему" }));

    await waitFor(() => {
      expect(mockedUpdate).toHaveBeenCalledWith("theme-1", {
        title: "Кислоты и основания",
        description: "Базовая тема",
        is_published: true,
      });
    });
    expect(onSaved).toHaveBeenCalled();
    expect(screen.getByRole("status")).toHaveTextContent("Сохранено");
  });
});
