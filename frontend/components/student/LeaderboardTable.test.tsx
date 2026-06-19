import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { LeaderboardTable } from "@/components/student/LeaderboardTable";
import { API_URL } from "@/lib/api/client";
import type { LeaderboardEntry, StudentStats } from "@/lib/api/types";

const studentId = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee";

const mockStats: StudentStats = {
  student_id: studentId,
  total_points: 120,
  week_points: 40,
  current_streak: 2,
  longest_streak: 5,
  last_active_date: "2026-06-18",
  tasks_solved: 8,
  total_minutes: 90,
  updated_at: "2026-06-19T10:00:00Z",
};

const weekEntries: LeaderboardEntry[] = [
  { rank: 1, display_name: "Химик-А", points: 40 },
  { rank: 2, display_name: "Ученик-bbbbbbbb", points: 25 },
];

const allTimeEntries: LeaderboardEntry[] = [
  { rank: 1, display_name: "Ученик-bbbbbbbb", points: 200 },
  { rank: 2, display_name: "Химик-А", points: 120 },
];

const server = setupServer(
  http.get(`${API_URL}/api/students/me/stats`, () => HttpResponse.json(mockStats)),
  http.get(`${API_URL}/api/leaderboard`, ({ request }) => {
    const period = new URL(request.url).searchParams.get("period");
    if (period === "all_time") {
      return HttpResponse.json(allTimeEntries);
    }
    return HttpResponse.json(weekEntries);
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("LeaderboardTable", () => {
  it("renders week leaderboard from GET /api/leaderboard", async () => {
    render(
      <LeaderboardTable
        currentStudentId={studentId}
        currentDisplayName="Химик-А"
      />,
    );

    expect(await screen.findByText("Химик-А")).toBeInTheDocument();
    expect(screen.getByText("40")).toBeInTheDocument();
    expect(screen.getByText("25")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Рейтинг" })).toBeInTheDocument();
  });

  it("highlights the current student row", async () => {
    render(
      <LeaderboardTable
        currentStudentId={studentId}
        currentDisplayName="Химик-А"
      />,
    );

    await screen.findByText("Химик-А");
    const marker = screen.getByText("(вы)");
    const currentRow = marker.closest("li");
    expect(currentRow).not.toBeNull();
    expect(currentRow).toHaveAttribute("aria-current", "true");
    expect(within(currentRow as HTMLElement).getByText("Химик-А")).toBeInTheDocument();
  });

  it("switches period to all_time and reloads data", async () => {
    const user = userEvent.setup();
    render(
      <LeaderboardTable
        currentStudentId={studentId}
        currentDisplayName="Химик-А"
      />,
    );

    expect(await screen.findByText("40")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "За всё время" }));

    await waitFor(() => {
      expect(screen.getByText("200")).toBeInTheDocument();
    });
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(screen.queryByText("25")).not.toBeInTheDocument();
  });

  it("shows error when leaderboard API fails", async () => {
    server.use(
      http.get(`${API_URL}/api/leaderboard`, () =>
        HttpResponse.json({ detail: "Forbidden" }, { status: 403 }),
      ),
    );

    render(<LeaderboardTable currentStudentId={studentId} />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Forbidden");
    });
  });

  it("shows empty state when leaderboard has no entries", async () => {
    server.use(
      http.get(`${API_URL}/api/leaderboard`, () => HttpResponse.json([])),
    );

    render(<LeaderboardTable currentStudentId={studentId} />);

    expect(
      await screen.findByText("Пока нет участников в рейтинге."),
    ).toBeInTheDocument();
  });
});
