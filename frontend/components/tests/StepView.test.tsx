import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StepView } from "@/components/tests/StepView";
import { checkStep, completeSession, getHint } from "@/lib/api/tests";
import type { TestSession } from "@/lib/api/types";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/lib/api/tests", () => ({
  checkStep: vi.fn(),
  getHint: vi.fn(),
  completeSession: vi.fn(),
}));

// QuestionContent fetches image blobs; stub it to keep the test focused on flow.
vi.mock("@/components/tests/QuestionContent", () => ({
  QuestionContent: ({ text }: { text: string }) => <p>{text}</p>,
}));

const mockedCheck = vi.mocked(checkStep);
const mockedHint = vi.mocked(getHint);
const mockedComplete = vi.mocked(completeSession);

const session: TestSession = {
  id: "sess-1",
  track: "ege",
  variant_ref: "001.txt",
  status: "in_progress",
  score: null,
  max_score: null,
  total_steps: 2,
  steps: [
    {
      position: 0,
      test_id: 11,
      type: 1,
      question: "Вопрос 1",
      options: null,
      status: "unseen",
      answer: null,
      is_correct: null,
      hint_used: false,
    },
    {
      position: 1,
      test_id: 12,
      type: 2,
      question: "Вопрос 2",
      options: null,
      status: "unseen",
      answer: null,
      is_correct: null,
      hint_used: false,
    },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("StepView", () => {
  it("checks an answer and shows instant feedback", async () => {
    mockedCheck.mockResolvedValue({
      position: 0,
      is_correct: true,
      status: "checked",
      detailed_explanation: "Разбор задания",
    });

    render(<StepView session={session} />);

    await userEvent.type(screen.getByLabelText("Ваш ответ"), "23");
    await userEvent.click(screen.getByRole("button", { name: "Проверить" }));

    expect(mockedCheck).toHaveBeenCalledWith("sess-1", 0, "23");
    expect(await screen.findByRole("status")).toHaveTextContent("Верно");
    expect(screen.getByText(/Разбор задания/)).toBeInTheDocument();
  });

  it("loads a hint only when requested", async () => {
    mockedHint.mockResolvedValue({ hint: "Смотри валентность" });

    render(<StepView session={session} />);

    expect(screen.queryByText(/Смотри валентность/)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Подсказка" }));

    expect(mockedHint).toHaveBeenCalledWith("sess-1", 0);
    expect(await screen.findByText(/Смотри валентность/)).toBeInTheDocument();
  });

  it("completes the test on the last step and navigates to summary", async () => {
    mockedComplete.mockResolvedValue({});

    render(<StepView session={session} />);

    await userEvent.click(screen.getByRole("button", { name: "Далее →" }));
    await userEvent.click(
      screen.getByRole("button", { name: "Завершить тест" }),
    );

    await waitFor(() => {
      expect(mockedComplete).toHaveBeenCalledWith("sess-1");
    });
    expect(push).toHaveBeenCalledWith(
      "/student/tests/sessions/sess-1/summary",
    );
  });
});
