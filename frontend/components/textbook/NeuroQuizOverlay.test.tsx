import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { NeuroQuizOverlay } from "@/components/textbook/NeuroQuizOverlay";
import {
  answerNeuroQuiz,
  getNeuroQuizSession,
  skipNeuroQuiz,
  voteNeuroQuiz,
} from "@/lib/api/neuroquiz";

vi.mock("@/lib/api/neuroquiz", () => ({
  getNeuroQuizSession: vi.fn(),
  answerNeuroQuiz: vi.fn(),
  skipNeuroQuiz: vi.fn(),
  voteNeuroQuiz: vi.fn(),
  warmupNeuroQuiz: vi.fn(),
}));

const mockedGet = vi.mocked(getNeuroQuizSession);
const mockedAnswer = vi.mocked(answerNeuroQuiz);
const mockedSkip = vi.mocked(skipNeuroQuiz);
const mockedVote = vi.mocked(voteNeuroQuiz);

const session = {
  topic: "Соли",
  chunk_idx: 0,
  scoring_enabled: true,
  questions: [
    {
      id: "q1",
      prompt: "Что такое соль?",
      options: [
        { id: "a", text: "Ионное соединение" },
        { id: "b", text: "Металл" },
        { id: "c", text: "Газ" },
        { id: "d", text: "Кислота" },
      ],
    },
    {
      id: "q2",
      prompt: "Формула NaCl?",
      options: [
        { id: "a", text: "NaCl" },
        { id: "b", text: "H2O" },
        { id: "c", text: "CO2" },
        { id: "d", text: "O2" },
      ],
    },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  mockedGet.mockReset();
  mockedAnswer.mockReset();
  mockedSkip.mockReset();
  mockedVote.mockReset();
  mockedGet.mockResolvedValue(session);
  mockedSkip.mockResolvedValue(undefined);
  mockedVote.mockResolvedValue(undefined);
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

describe("NeuroQuizOverlay", () => {
  it("loads questions when open", async () => {
    render(
      <NeuroQuizOverlay
        topic="Соли"
        chunkIdx={0}
        open
        onSkip={vi.fn()}
        onComplete={vi.fn()}
      />,
    );

    expect(await screen.findByText("Что такое соль?")).toBeInTheDocument();
    expect(screen.getByText("Вопрос 1 из 2")).toBeInTheDocument();
    expect(mockedGet).toHaveBeenCalledWith("Соли", 0);
  });

  it("locks options after answer and shows vote icons under the prompt", async () => {
    mockedAnswer.mockResolvedValue({
      correct: true,
      correct_option_id: "a",
      explanation: "Верно",
      points_awarded: 1,
      quiz_completed: false,
    });

    render(
      <NeuroQuizOverlay
        topic="Соли"
        chunkIdx={0}
        open
        onSkip={vi.fn()}
        onComplete={vi.fn()}
      />,
    );

    await screen.findByText("Что такое соль?");
    expect(
      screen.queryByRole("button", { name: "Полезно" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Плохой вопрос" }),
    ).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Ионное соединение" }));

    expect(await screen.findByText("Верно! +1 балл")).toBeInTheDocument();
    const like = screen.getByRole("button", { name: "Полезно" });
    const dislike = screen.getByRole("button", { name: "Плохой вопрос" });
    expect(like).toBeInTheDocument();
    expect(dislike).toBeInTheDocument();
    // Icons under the question: vote group appears before answer options in DOM order
    const prompt = screen.getByText("Что такое соль?");
    expect(prompt.compareDocumentPosition(like) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const optionsGroup = screen.getByRole("group", { name: "Варианты ответа" });
    expect(like.compareDocumentPosition(optionsGroup) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Ионное соединение" }),
    ).toBeDisabled();
    expect(screen.getByTestId("neuroquiz-salute")).toBeInTheDocument();
  });

  it("skips salute animation when prefers-reduced-motion", async () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: query.includes("prefers-reduced-motion"),
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    mockedAnswer.mockResolvedValue({
      correct: true,
      correct_option_id: "a",
      explanation: "Верно",
      points_awarded: 1,
      quiz_completed: false,
    });

    render(
      <NeuroQuizOverlay
        topic="Соли"
        chunkIdx={0}
        open
        onSkip={vi.fn()}
        onComplete={vi.fn()}
      />,
    );

    await screen.findByText("Что такое соль?");
    await userEvent.click(screen.getByRole("button", { name: "Ионное соединение" }));
    expect(await screen.findByText("Верно! +1 балл")).toBeInTheDocument();
    expect(screen.queryByTestId("neuroquiz-salute")).not.toBeInTheDocument();
  });

  it("calls onSkip for skip button and Escape", async () => {
    const onSkip = vi.fn();
    render(
      <NeuroQuizOverlay
        topic="Соли"
        chunkIdx={0}
        open
        onSkip={onSkip}
        onComplete={vi.fn()}
      />,
    );

    await screen.findByText("Что такое соль?");
    await userEvent.click(screen.getByRole("button", { name: "Пропустить квиз" }));
    expect(onSkip).toHaveBeenCalled();
    expect(mockedSkip).toHaveBeenCalledWith("Соли", 0);

    onSkip.mockClear();
    await userEvent.keyboard("{Escape}");
    await waitFor(() => expect(onSkip).toHaveBeenCalled());
  });

  it("does not render when closed", () => {
    render(
      <NeuroQuizOverlay
        topic="Соли"
        chunkIdx={0}
        open={false}
        onSkip={vi.fn()}
        onComplete={vi.fn()}
      />,
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows correct option and explanation after a wrong answer without salute", async () => {
    mockedAnswer.mockResolvedValue({
      correct: false,
      correct_option_id: "a",
      explanation: "Соль — ионное соединение",
      points_awarded: 0,
      quiz_completed: false,
    });

    render(
      <NeuroQuizOverlay
        topic="Соли"
        chunkIdx={0}
        open
        onSkip={vi.fn()}
        onComplete={vi.fn()}
      />,
    );

    await screen.findByText("Что такое соль?");
    await userEvent.click(screen.getByRole("button", { name: "Металл" }));

    expect(await screen.findByText("Неверно")).toBeInTheDocument();
    expect(screen.getByText("Соль — ионное соединение")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ионное соединение" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Металл" })).toBeDisabled();
    expect(screen.queryByTestId("neuroquiz-salute")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Полезно" })).toBeInTheDocument();
  });

  it("sends vote only after answering", async () => {
    mockedAnswer.mockResolvedValue({
      correct: true,
      correct_option_id: "a",
      explanation: "Верно",
      points_awarded: 1,
      quiz_completed: false,
    });

    render(
      <NeuroQuizOverlay
        topic="Соли"
        chunkIdx={0}
        open
        onSkip={vi.fn()}
        onComplete={vi.fn()}
      />,
    );

    await screen.findByText("Что такое соль?");
    expect(mockedVote).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: "Ионное соединение" }));
    await screen.findByText("Верно! +1 балл");
    await userEvent.click(screen.getByRole("button", { name: "Полезно" }));
    expect(mockedVote).toHaveBeenCalledWith("q1", "like");
  });

  it("calls onComplete after answering the last question and clicking Далее", async () => {
    const onComplete = vi.fn();
    mockedAnswer
      .mockResolvedValueOnce({
        correct: true,
        correct_option_id: "a",
        explanation: "Верно",
        points_awarded: 1,
        quiz_completed: false,
      })
      .mockResolvedValueOnce({
        correct: true,
        correct_option_id: "a",
        explanation: "Верно",
        points_awarded: 1,
        quiz_completed: true,
      });

    render(
      <NeuroQuizOverlay
        topic="Соли"
        chunkIdx={0}
        open
        onSkip={vi.fn()}
        onComplete={onComplete}
      />,
    );

    await screen.findByText("Что такое соль?");
    await userEvent.click(screen.getByRole("button", { name: "Ионное соединение" }));
    await screen.findByText("Верно! +1 балл");
    await userEvent.click(screen.getByRole("button", { name: "Далее" }));

    expect(await screen.findByText("Формула NaCl?")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "NaCl" }));
    await screen.findByText("Верно! +1 балл");
    await userEvent.click(screen.getByRole("button", { name: "Далее" }));

    expect(onComplete).toHaveBeenCalledTimes(1);
  });

  it("reloads remaining questions after last cached answer when quiz_completed is false", async () => {
    const onComplete = vi.fn();
    // Mid-pass resume: server returns only unanswered questions (one left in cache).
    mockedGet
      .mockResolvedValueOnce({
        ...session,
        questions: [session.questions[0]],
      })
      .mockResolvedValueOnce({
        ...session,
        questions: [session.questions[1]],
      });
    mockedAnswer.mockResolvedValue({
      correct: true,
      correct_option_id: "a",
      explanation: "Верно",
      points_awarded: 1,
      quiz_completed: false,
    });

    render(
      <NeuroQuizOverlay
        topic="Соли"
        chunkIdx={0}
        open
        onSkip={vi.fn()}
        onComplete={onComplete}
      />,
    );

    await screen.findByText("Что такое соль?");
    expect(screen.getByText("Вопрос 1 из 1")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Ионное соединение" }));
    await screen.findByText("Верно! +1 балл");
    await userEvent.click(screen.getByRole("button", { name: "Далее" }));

    expect(onComplete).not.toHaveBeenCalled();
    expect(await screen.findByText("Формула NaCl?")).toBeInTheDocument();
    expect(screen.getByText("Вопрос 1 из 1")).toBeInTheDocument();
    expect(mockedGet).toHaveBeenCalledTimes(2);
  });

  it("calls onComplete when reload after last answer returns no remaining questions", async () => {
    const onComplete = vi.fn();
    mockedGet
      .mockResolvedValueOnce({
        ...session,
        questions: [session.questions[0]],
      })
      .mockResolvedValueOnce({
        ...session,
        questions: [],
      });
    mockedAnswer.mockResolvedValue({
      correct: true,
      correct_option_id: "a",
      explanation: "Верно",
      points_awarded: 1,
      quiz_completed: false,
    });

    render(
      <NeuroQuizOverlay
        topic="Соли"
        chunkIdx={0}
        open
        onSkip={vi.fn()}
        onComplete={onComplete}
      />,
    );

    await screen.findByText("Что такое соль?");
    await userEvent.click(screen.getByRole("button", { name: "Ионное соединение" }));
    await screen.findByText("Верно! +1 балл");
    await userEvent.click(screen.getByRole("button", { name: "Далее" }));

    await waitFor(() => expect(onComplete).toHaveBeenCalledTimes(1));
    expect(mockedGet).toHaveBeenCalledTimes(2);
  });

  it("after reopen with unanswered-only session, answers index 0 without 409", async () => {
    mockedGet.mockResolvedValue({
      ...session,
      questions: [session.questions[1]],
    });
    mockedAnswer.mockResolvedValue({
      correct: true,
      correct_option_id: "a",
      explanation: "Верно",
      points_awarded: 1,
      quiz_completed: false,
    });

    render(
      <NeuroQuizOverlay
        topic="Соли"
        chunkIdx={0}
        open
        onSkip={vi.fn()}
        onComplete={vi.fn()}
      />,
    );

    expect(await screen.findByText("Формула NaCl?")).toBeInTheDocument();
    expect(screen.getByText("Вопрос 1 из 1")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "NaCl" }));
    expect(mockedAnswer).toHaveBeenCalledWith("Соли", 0, "q2", "a");
    expect(await screen.findByText("Верно! +1 балл")).toBeInTheDocument();
  });

  it("shows Retry and Skip when session load fails", async () => {
    mockedGet.mockRejectedValueOnce(new Error("network"));
    const onSkip = vi.fn();

    render(
      <NeuroQuizOverlay
        topic="Соли"
        chunkIdx={0}
        open
        onSkip={onSkip}
        onComplete={vi.fn()}
      />,
    );

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Повторить" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Пропустить квиз" }));
    expect(onSkip).toHaveBeenCalled();
  });

  it("keeps Далее disabled until the student answers", async () => {
    render(
      <NeuroQuizOverlay
        topic="Соли"
        chunkIdx={0}
        open
        onSkip={vi.fn()}
        onComplete={vi.fn()}
      />,
    );

    await screen.findByText("Что такое соль?");
    expect(screen.getByRole("button", { name: "Далее" })).toBeDisabled();
  });
});
