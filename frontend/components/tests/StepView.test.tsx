import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StepView } from "@/components/tests/StepView";
import { checkStep, compareStep, completeSession } from "@/lib/api/tests";
import type { TestSession } from "@/lib/api/types";

const push = vi.fn();
const openTutor = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/lib/tutor/TutorChatContext", () => ({
  useTutorChat: () => ({ openTutor }),
}));

vi.mock("@/lib/api/tests", () => ({
  checkStep: vi.fn(),
  compareStep: vi.fn(),
  completeSession: vi.fn(),
}));

vi.mock("@/lib/api/uploads", () => ({
  uploadImage: vi.fn(),
}));

vi.mock("@/components/tests/QuestionContent", () => ({
  QuestionContent: ({ text }: { text: string }) => <p>{text}</p>,
}));

vi.mock("@/components/tests/CustomQuestionContent", () => ({
  CustomQuestionContent: ({ blocks }: { blocks: { content?: string }[] }) => (
    <p>{blocks[0]?.content ?? "custom"}</p>
  ),
}));

const mockedCheck = vi.mocked(checkStep);
const mockedCompare = vi.mocked(compareStep);
const mockedComplete = vi.mocked(completeSession);

const session: TestSession = {
  id: "sess-1",
  track: "ege",
  variant_ref: "001.txt",
  homework_assignment_id: null,
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
      status: "checked",
      answer: "23",
      is_correct: true,
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
  it("renders step dots with current step label", () => {
    render(<StepView session={session} />);

    expect(screen.getByText("Шаг 2 из 2")).toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });

  it("opens the first unchecked step on entry", () => {
    render(<StepView session={session} />);

    expect(screen.getByText("Вопрос 2")).toBeInTheDocument();
    expect(screen.getByLabelText("Ваш ответ")).toHaveValue("");
  });

  it("does not show hint or explanation controls", () => {
    render(<StepView session={session} />);

    expect(screen.queryByRole("button", { name: "Подсказка" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Разбор" })).not.toBeInTheDocument();
    expect(screen.queryByText(/Разбор:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Подсказка:/)).not.toBeInTheDocument();
  });

  it("checks an answer and shows instant feedback without explanation", async () => {
    const freshSession: TestSession = {
      ...session,
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
        session.steps[1],
      ],
    };

    mockedCheck.mockResolvedValue({
      position: 0,
      is_correct: true,
      status: "checked",
    });

    render(<StepView session={freshSession} />);

    await userEvent.type(screen.getByLabelText("Ваш ответ"), "23");
    await userEvent.click(screen.getByRole("button", { name: "Проверить" }));

    expect(mockedCheck).toHaveBeenCalledWith("sess-1", 0, "23");
    expect(await screen.findByRole("status")).toHaveTextContent("Верно");
    expect(screen.queryByText(/Разбор/)).not.toBeInTheDocument();
  });

  it("completes the test on the last step and navigates to summary", async () => {
    mockedComplete.mockResolvedValue({});

    render(<StepView session={session} />);

    await userEvent.click(screen.getByRole("button", { name: "Завершить" }));

    await waitFor(() => {
      expect(mockedComplete).toHaveBeenCalledWith("sess-1");
    });
    expect(push).toHaveBeenCalledWith(
      "/student/tests/sessions/sess-1/summary",
    );
  });

  it("does not show ask-tutor before check or on correct answer", () => {
    render(<StepView session={session} />);

    expect(
      screen.queryByRole("button", { name: "Спросить советчика" }),
    ).not.toBeInTheDocument();
  });

  it("opens tutor with explain_incorrect_step context after wrong answer", async () => {
    const freshSession: TestSession = {
      ...session,
      steps: [
        {
          position: 0,
          test_id: 42,
          type: 1,
          question: "Вопрос 1",
          options: null,
          status: "unseen",
          answer: null,
          is_correct: null,
          hint_used: false,
        },
      ],
      total_steps: 1,
    };

    mockedCheck.mockResolvedValue({
      position: 0,
      is_correct: false,
      status: "checked",
    });

    render(<StepView session={freshSession} />);

    await userEvent.type(screen.getByLabelText("Ваш ответ"), "99");
    await userEvent.click(screen.getByRole("button", { name: "Проверить" }));

    const askButton = await screen.findByRole("button", {
      name: "Спросить советчика",
    });
    await userEvent.click(askButton);

    expect(openTutor).toHaveBeenCalledWith({
      pageContext: {
        test_session_id: "sess-1",
        step_position: 0,
        test_id: 42,
        solve_mode: "explain_incorrect_step",
      },
      initialMessage:
        "Разбери задание 42. Мой ответ: «99». Объясни, в чём ошибка, и сравни с правильным ответом.",
      autoSendInitialMessage: true,
    });
  });

  it("uses compare for self_check custom steps and shows reference", async () => {
    const customSession: TestSession = {
      id: "sess-custom",
      track: "ege",
      source: "custom",
      variant_ref: null,
      homework_assignment_id: null,
      custom_theme_id: "theme-1",
      status: "in_progress",
      score: null,
      max_score: null,
      total_steps: 1,
      created_at: "2026-01-01T00:00:00Z",
      steps: [
        {
          position: 0,
          test_id: null,
          custom_task_id: "task-1",
          type: null,
          question: null,
          options: null,
          question_blocks: [{ type: "text", content: "Опишите реакцию" }],
          grading_mode: "self_check",
          status: "unseen",
          answer: null,
          is_correct: null,
          hint_used: false,
        },
      ],
    };

    mockedCompare.mockResolvedValue({
      position: 0,
      status: "checked",
      reference_answer: [{ type: "text", content: "Эталон" }],
    });

    render(<StepView session={customSession} />);

    expect(screen.getByText("Опишите реакцию")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Спросить советчика" }),
    ).not.toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Ваш ответ"), "мой ответ");
    await userEvent.click(screen.getByRole("button", { name: "Сравнить ответ" }));

    expect(mockedCompare).toHaveBeenCalledWith(
      "sess-custom",
      0,
      "мой ответ",
    );
    expect(await screen.findByText("Эталон")).toBeInTheDocument();
    expect(mockedCheck).not.toHaveBeenCalled();
  });
});
