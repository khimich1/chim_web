import {
  afterAll,
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { ResumeSessionCards } from "@/components/student/ResumeSessionCards";
import { API_URL } from "@/lib/api/client";
import type { HomeworkAssignment } from "@/lib/api/types";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

const homework: HomeworkAssignment[] = [
  {
    id: "hw-1",
    student_id: "s1",
    student_email: null,
    title: "Алканы",
    description: null,
    due_at: null,
    items: [{ kind: "test_variant", variant: "001.txt" }],
    status: "in_progress",
    created_at: "2026-06-17T10:00:00Z",
    submission: null,
    progress: [],
    active_test_session_id: "sess-hw-1",
  },
];

const homeworkSession = {
  id: "sess-hw-1",
  track: "ege" as const,
  variant_ref: null,
  homework_assignment_id: "hw-1",
  status: "in_progress" as const,
  score: null,
  max_score: null,
  total_steps: 5,
  created_at: "2026-06-19T08:00:00Z",
  steps: [
    {
      position: 1,
      test_id: 1,
      type: 1,
      question: "Q1",
      options: null,
      status: "checked" as const,
      answer: "1",
      is_correct: true,
      hint_used: false,
    },
    {
      position: 2,
      test_id: 2,
      type: 1,
      question: "Q2",
      options: null,
      status: "unseen" as const,
      answer: null,
      is_correct: null,
      hint_used: false,
    },
  ],
};

const practiceSession = {
  id: "sess-practice-1",
  track: "ege" as const,
  variant_ref: "002.txt",
  homework_assignment_id: null,
  status: "in_progress" as const,
  score: null,
  max_score: null,
  total_steps: 3,
  created_at: "2026-06-19T09:30:00Z",
  steps: [],
};

const server = setupServer(
  http.get(`${API_URL}/api/tests/sessions/sess-hw-1`, () =>
    HttpResponse.json(homeworkSession),
  ),
  http.get(`${API_URL}/api/tests/sessions/active`, ({ request }) => {
    const url = new URL(request.url);
    if (url.searchParams.get("variant_ref") === "002.txt") {
      return HttpResponse.json({ session_id: "sess-practice-1" });
    }
    return HttpResponse.json({ session_id: null });
  }),
  http.get(`${API_URL}/api/tests/sessions/sess-practice-1`, () =>
    HttpResponse.json(practiceSession),
  ),
);

beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  vi.clearAllMocks();
});
afterAll(() => server.close());

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ResumeSessionCards", () => {
  it("renders homework and practice resume cards with elapsed time", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-06-19T10:00:00Z"));

    render(
      <ResumeSessionCards
        homework={homework}
        variants={[{ filename: "002.txt" }]}
      />,
    );

    expect(await screen.findByRole("heading", { name: "Алканы" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Вариант 002" })).toBeInTheDocument();
    expect(screen.getByText(/Прошло 2 ч · 1 \/ 5 шагов/)).toBeInTheDocument();
    expect(screen.getByText(/Прошло 30 мин · 0 \/ 3 шагов/)).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Продолжить" })).toHaveLength(2);

    vi.useRealTimers();
  });

  it("navigates to session on continue", async () => {
    render(
      <ResumeSessionCards homework={homework} variants={[]} />,
    );

    await userEvent.click(
      await screen.findByRole("button", { name: "Продолжить" }),
    );

    expect(push).toHaveBeenCalledWith("/student/tests/sessions/sess-hw-1");
  });

  it("renders nothing when there are no in_progress sessions", async () => {
    server.use(
      http.get(`${API_URL}/api/tests/sessions/sess-hw-1`, () =>
        HttpResponse.json({ ...homeworkSession, status: "completed" }),
      ),
    );

    const { container } = render(
      <ResumeSessionCards homework={homework} variants={[]} />,
    );

    await waitFor(() => {
      expect(container).toBeEmptyDOMElement();
    });
  });

  it("shows error when session API fails", async () => {
    server.use(
      http.get(`${API_URL}/api/tests/sessions/sess-hw-1`, () =>
        HttpResponse.json({ detail: "Not found" }, { status: 404 }),
      ),
    );

    render(<ResumeSessionCards homework={homework} variants={[]} />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Not found");
    });
  });
});
