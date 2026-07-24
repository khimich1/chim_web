import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TemplateList } from "@/components/homework/TemplateList";
import { deleteHomeworkTemplate } from "@/lib/api/templates";
import type { HomeworkTemplate } from "@/lib/api/types";

const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

vi.mock("@/lib/api/templates", () => ({
  deleteHomeworkTemplate: vi.fn(),
}));

const mockedDelete = vi.mocked(deleteHomeworkTemplate);

const template: HomeworkTemplate = {
  id: "tpl-1",
  teacher_id: "t1",
  title: "Шаблон: алканы",
  description: "Прочитать",
  items: [{ kind: "lecture", topic: "Алканы" }],
  created_at: "2026-07-23T10:00:00Z",
  updated_at: "2026-07-23T10:00:00Z",
};

beforeEach(() => {
  vi.clearAllMocks();
  mockedDelete.mockResolvedValue(undefined);
  vi.spyOn(window, "confirm").mockReturnValue(true);
});

describe("TemplateList", () => {
  it("renders empty state", () => {
    render(<TemplateList templates={[]} />);
    expect(screen.getByText(/Шаблонов пока нет/)).toBeInTheDocument();
  });

  it("renders template cards with edit links", () => {
    render(<TemplateList templates={[template]} />);
    expect(
      screen.getByRole("heading", { name: "Шаблон: алканы" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Шаблон: алканы" }),
    ).toHaveAttribute("href", "/teacher/homework/templates/tpl-1");
  });

  it("deletes template after confirm", async () => {
    render(<TemplateList templates={[template]} />);
    fireEvent.click(screen.getByRole("button", { name: "Удалить" }));
    await waitFor(() => {
      expect(mockedDelete).toHaveBeenCalledWith("tpl-1");
    });
    expect(refresh).toHaveBeenCalled();
  });
});
