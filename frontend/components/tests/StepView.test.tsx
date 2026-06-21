import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StepView } from "@/components/tests/StepView";
import { uploadImage } from "@/lib/api/uploads";
import { attachAnswerImage, checkStep, compareStep, completeSession, getSession } from "@/lib/api/tests";
import { createHandoff } from "@/lib/api/handoff";
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
  attachAnswerImage: vi.fn(),
  getSession: vi.fn(),
}));

vi.mock("@/lib/api/handoff", () => ({
  createHandoff: vi.fn(),
}));

vi.mock("react-qr-code", () => ({
  default: ({ value }: { value: string }) => <div data-testid="qr-code">{value}</div>,
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
const mockedAttach = vi.mocked(attachAnswerImage);
const mockedUpload = vi.mocked(uploadImage);
const mockedGetSession = vi.mocked(getSession);
const mockedCreateHandoff = vi.mocked(createHandoff);

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

  it("uses compare for exam content self_check (type 29) and shows reference blocks", async () => {
    const examSession: TestSession = {
      id: "sess-exam-written",
      track: "ege",
      source: "exam",
      variant_ref: "001.txt",
      homework_assignment_id: null,
      status: "in_progress",
      score: null,
      max_score: null,
      total_steps: 1,
      created_at: "2026-01-01T00:00:00Z",
      steps: [
        {
          position: 0,
          test_id: 100,
          type: 29,
          question: "Written Q29",
          options: null,
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
      reference_answer: [
        { type: "text", content: "Разбор " },
        { type: "image", url: "/api/tests/images/%D0%BE%D1%82%D0%B2%D0%B5%D1%820001.png" },
      ],
    });

    render(<StepView session={examSession} />);

    expect(screen.getByText("Written Q29")).toBeInTheDocument();
    expect(screen.getByText("Тип 29")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Прикрепить с этого устройства/i }),
    ).not.toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Ваш ответ"), "мой разбор");
    await userEvent.click(screen.getByRole("button", { name: "Сравнить ответ" }));

    expect(mockedCompare).toHaveBeenCalledWith(
      "sess-exam-written",
      0,
      "мой разбор",
    );
    expect(await screen.findByText("Разбор")).toBeInTheDocument();
    expect(mockedCheck).not.toHaveBeenCalled();
  });

  it("requires photo for exam content self_check in homework sessions", async () => {
    const homeworkExamSession: TestSession = {
      id: "sess-hw-exam",
      track: "ege",
      source: "exam",
      variant_ref: "001.txt",
      homework_assignment_id: "hw-1",
      status: "in_progress",
      score: null,
      max_score: null,
      total_steps: 1,
      created_at: "2026-01-01T00:00:00Z",
      steps: [
        {
          position: 0,
          test_id: 100,
          type: 30,
          question: "Written Q30",
          options: null,
          grading_mode: "self_check",
          status: "unseen",
          answer: null,
          is_correct: null,
          hint_used: false,
        },
      ],
    };

    render(<StepView session={homeworkExamSession} />);

    expect(
      screen.getByRole("button", { name: "Сравнить ответ" }),
    ).toBeDisabled();
    expect(
      screen.getByLabelText(/Прикрепить с этого устройства/i),
    ).toBeInTheDocument();
  });

  it("shows step count up to 34 steps", () => {
    const longSession: TestSession = {
      ...session,
      total_steps: 34,
      created_at: "2026-01-01T00:00:00Z",
      steps: Array.from({ length: 34 }, (_, index) => ({
        position: index,
        test_id: index + 1,
        type: index + 1,
        question: `Q${index + 1}`,
        options: null,
        status: "unseen" as const,
        answer: null,
        is_correct: null,
        hint_used: false,
        grading_mode: index >= 28 ? ("self_check" as const) : undefined,
      })),
    };

    render(<StepView session={longSession} />);

    expect(screen.getByText("Шаг 1 из 34")).toBeInTheDocument();
  });

  it("hides photo upload in practice self_check mode", () => {
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

    render(<StepView session={customSession} />);

    expect(
      screen.queryByRole("button", { name: /Прикрепить фото решения/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Сравнить ответ" }),
    ).not.toBeDisabled();
  });

  it("requires photo before compare in homework self_check mode", async () => {
    const homeworkSession: TestSession = {
      id: "sess-hw",
      track: "ege",
      source: "custom",
      variant_ref: null,
      homework_assignment_id: "hw-1",
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
          question_blocks: [{ type: "text", content: "Решение" }],
          grading_mode: "self_check",
          status: "unseen",
          answer: null,
          is_correct: null,
          hint_used: false,
        },
      ],
    };

    mockedUpload.mockResolvedValue({
      id: "img-1",
      url: "/api/uploads/images/img-1",
    });
    mockedAttach.mockResolvedValue({
      position: 0,
      answer_image_id: "img-1",
      answer_image_url: "/api/uploads/images/img-1",
    });
    mockedCompare.mockResolvedValue({
      position: 0,
      status: "checked",
      reference_answer: [{ type: "text", content: "Эталон" }],
    });

    render(<StepView session={homeworkSession} />);

    const compareButton = screen.getByRole("button", { name: "Сравнить ответ" });
    expect(compareButton).toBeDisabled();

    const fileInput = screen.getByLabelText(/Прикрепить с этого устройства/i);
    const file = new File(["photo"], "work.jpg", { type: "image/jpeg" });
    await userEvent.upload(fileInput, file);

    await waitFor(() => {
      expect(mockedUpload).toHaveBeenCalled();
      expect(mockedAttach).toHaveBeenCalledWith("sess-hw", 0, "img-1");
    });

    expect(compareButton).not.toBeDisabled();
    await userEvent.click(compareButton);
    expect(mockedCompare).toHaveBeenCalledWith("sess-hw", 0, "");
  });

  it("creates handoff QR and polls until photo arrives", async () => {
    const homeworkSession: TestSession = {
      id: "sess-hw",
      track: "ege",
      source: "custom",
      variant_ref: null,
      homework_assignment_id: "hw-1",
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
          question_blocks: [{ type: "text", content: "Решение" }],
          grading_mode: "self_check",
          status: "unseen",
          answer: null,
          is_correct: null,
          hint_used: false,
        },
      ],
    };

    mockedCreateHandoff.mockResolvedValue({
      token: "handoff-token",
      capture_url: "http://localhost:3000/student/capture/handoff-token",
      expires_at: "2026-06-20T12:00:00Z",
    });
    const sessionWithPhoto: TestSession = {
      ...homeworkSession,
      steps: [
        {
          ...homeworkSession.steps[0],
          answer_image_id: "img-phone",
          answer_image_url: "/api/uploads/images/img-phone",
        },
      ],
    };
    mockedGetSession
      .mockResolvedValueOnce(homeworkSession)
      .mockResolvedValue(sessionWithPhoto);

    render(<StepView session={homeworkSession} />);

    await userEvent.click(
      screen.getByRole("button", { name: "Сфотографировать с телефона" }),
    );

    expect(mockedCreateHandoff).toHaveBeenCalledWith("sess-hw", 0);
    await waitFor(() => {
      expect(screen.getByTestId("qr-code")).toHaveTextContent(
        "http://localhost:3000/student/capture/handoff-token",
      );
    });

    await waitFor(
      () => {
        expect(mockedGetSession).toHaveBeenCalledWith("sess-hw");
        expect(screen.getByText("Фото получено с телефона")).toBeInTheDocument();
      },
      { timeout: 5000 },
    );
  });
});
