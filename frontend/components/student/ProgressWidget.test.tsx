import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { ProgressWidget } from "@/components/student/ProgressWidget";
import { API_URL } from "@/lib/api/client";
import type { StudentStats } from "@/lib/api/types";

const mockStats: StudentStats = {
  student_id: "11111111-1111-1111-1111-111111111111",
  total_points: 240,
  week_points: 80,
  current_streak: 3,
  longest_streak: 7,
  last_active_date: "2026-06-18",
  tasks_solved: 12,
  total_minutes: 95,
  updated_at: "2026-06-19T10:00:00Z",
};

const server = setupServer(
  http.get(`${API_URL}/api/students/me/stats`, () => HttpResponse.json(mockStats)),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("ProgressWidget", () => {
  it("renders stats from GET /api/students/me/stats", async () => {
    render(<ProgressWidget />);

    expect(await screen.findByText("80")).toBeInTheDocument();
    expect(screen.getByText("240")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText(/12/)).toBeInTheDocument();
    expect(screen.getByText(/1 ч 35 мин в тестах/)).toBeInTheDocument();
    expect(screen.getByText(/рекорд 7/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Мой прогресс" })).toBeInTheDocument();
  });

  it("shows error when stats API fails", async () => {
    server.use(
      http.get(`${API_URL}/api/students/me/stats`, () =>
        HttpResponse.json({ detail: "Forbidden" }, { status: 403 }),
      ),
    );

    render(<ProgressWidget />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Forbidden");
    });
  });

  it("renders initialStats without fetching", () => {
    const initial: StudentStats = { ...mockStats, week_points: 50 };
    render(<ProgressWidget initialStats={initial} />);

    expect(screen.getByText("50")).toBeInTheDocument();
    expect(screen.queryByText("Загрузка…")).not.toBeInTheDocument();
  });
});
