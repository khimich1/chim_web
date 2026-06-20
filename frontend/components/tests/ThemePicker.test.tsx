import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ThemePicker } from "@/components/tests/ThemePicker";
import { createSession, getActiveSession } from "@/lib/api/tests";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/lib/api/tests", () => ({
  createSession: vi.fn(),
  getActiveSession: vi.fn(),
}));

const mockedCreate = vi.mocked(createSession);
const mockedActive = vi.mocked(getActiveSession);

const themes = [
  {
    id: "theme-1",
    title: "Органика",
    description: "Введение",
    task_count: 2,
    sort_order: 0,
  },
];

beforeEach(() => {
  vi.clearAllMocks();
  mockedActive.mockResolvedValue({ session_id: null });
});

describe("ThemePicker", () => {
  it("starts a custom theme session", async () => {
    mockedCreate.mockResolvedValue({
      id: "sess-custom",
      track: "ege",
      source: "custom",
      variant_ref: null,
      homework_assignment_id: null,
      custom_theme_id: "theme-1",
      status: "in_progress",
      score: null,
      max_score: null,
      total_steps: 2,
      steps: [],
      created_at: "2026-01-01T00:00:00Z",
    });

    render(<ThemePicker themes={themes} />);

    await userEvent.click(screen.getByRole("button", { name: "Начать" }));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith({
        customThemeId: "theme-1",
      });
    });
    expect(push).toHaveBeenCalledWith("/student/tests/sessions/sess-custom");
  });

  it("shows continue when active session exists", async () => {
    mockedActive.mockResolvedValue({ session_id: "sess-active" });

    render(<ThemePicker themes={themes} />);

    expect(
      await screen.findByRole("button", { name: "Продолжить" }),
    ).toBeInTheDocument();
  });
});
