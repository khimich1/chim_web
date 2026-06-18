import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TutorChatOverlay } from "@/components/tutor/TutorChatOverlay";
import {
  createTutorSession,
  getTutorHealth,
  getTutorSession,
  sendTutorMessage,
} from "@/lib/api/tutor";
import { ApiError } from "@/lib/api/client";
import { TutorChatProvider } from "@/lib/tutor/TutorChatContext";

let pathname = "/student/textbook/Алканы";

vi.mock("next/navigation", () => ({
  usePathname: () => pathname,
}));

vi.mock("@/lib/api/tutor", () => ({
  getTutorHealth: vi.fn(),
  createTutorSession: vi.fn(),
  getTutorSession: vi.fn(),
  sendTutorMessage: vi.fn(),
}));

const mockedHealth = vi.mocked(getTutorHealth);
const mockedCreate = vi.mocked(createTutorSession);
const mockedGet = vi.mocked(getTutorSession);
const mockedSend = vi.mocked(sendTutorMessage);

function primeHappyPath() {
  mockedHealth.mockResolvedValue({
    openai_configured: true,
    rag_index_exists: true,
  });
  mockedCreate.mockResolvedValue({
    id: "session-1",
    role_context: "student",
    page_context: { topic: "Алканы" },
    created_at: "2026-06-17T10:00:00Z",
    updated_at: "2026-06-17T10:00:00Z",
    message_count: 0,
  });
  mockedGet.mockResolvedValue({
    id: "session-1",
    role_context: "student",
    page_context: { topic: "Алканы" },
    created_at: "2026-06-17T10:00:00Z",
    updated_at: "2026-06-17T10:00:00Z",
    message_count: 0,
    messages: [],
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  pathname = "/student/textbook/Алканы";
});

function renderOverlay() {
  return render(
    <TutorChatProvider>
      <TutorChatOverlay />
    </TutorChatProvider>,
  );
}

describe("TutorChatOverlay", () => {
  it("opens the chat with the current page context", async () => {
    primeHappyPath();
    renderOverlay();

    await userEvent.click(
      screen.getByRole("button", { name: "AI-советчик по химии" }),
    );

    await waitFor(() =>
      expect(mockedCreate).toHaveBeenCalledWith({ topic: "Алканы" }),
    );
    expect(mockedHealth).toHaveBeenCalled();
    expect(
      await screen.findByText(/Задайте вопрос по теории/),
    ).toBeInTheDocument();
  });

  it("sends a message and renders the assistant reply", async () => {
    primeHappyPath();
    mockedSend.mockResolvedValue({
      message_id: "m1",
      role: "assistant",
      content: "Алканы малореакционны.",
      sources: [],
    });
    renderOverlay();

    await userEvent.click(
      screen.getByRole("button", { name: "AI-советчик по химии" }),
    );
    await screen.findByText(/Задайте вопрос по теории/);

    await userEvent.type(
      screen.getByPlaceholderText("Ваш вопрос…"),
      "Что такое алканы?",
    );
    await userEvent.click(screen.getByRole("button", { name: "Отправить" }));

    expect(await screen.findByText("Что такое алканы?")).toBeInTheDocument();
    expect(
      await screen.findByText("Алканы малореакционны."),
    ).toBeInTheDocument();
  });

  it("rolls back the optimistic message and restores input on error", async () => {
    primeHappyPath();
    mockedSend.mockRejectedValue(new ApiError(503, "Агент недоступен"));
    renderOverlay();

    await userEvent.click(
      screen.getByRole("button", { name: "AI-советчик по химии" }),
    );
    await screen.findByText(/Задайте вопрос по теории/);

    const input = screen.getByPlaceholderText("Ваш вопрос…");
    await userEvent.type(input, "Что такое алканы?");
    await userEvent.click(screen.getByRole("button", { name: "Отправить" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Агент недоступен",
    );
    // Optimistic user bubble removed and the text returned to the input.
    await waitFor(() =>
      expect(screen.getByPlaceholderText("Ваш вопрос…")).toHaveValue(
        "Что такое алканы?",
      ),
    );
  });

  it("creates a new session after navigation (I1: no stale page_context)", async () => {
    primeHappyPath();
    const { rerender } = renderOverlay();

    await userEvent.click(
      screen.getByRole("button", { name: "AI-советчик по химии" }),
    );
    await waitFor(() =>
      expect(mockedCreate).toHaveBeenCalledWith({ topic: "Алканы" }),
    );

    // Close chat, navigate to a test page, reopen → fresh session with new context.
    await userEvent.click(screen.getByRole("button", { name: "Закрыть чат" }));
    pathname = "/student/tests/sessions/abc-123";
    rerender(
      <TutorChatProvider>
        <TutorChatOverlay />
      </TutorChatProvider>,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "AI-советчик по химии" }),
    );
    await waitFor(() =>
      expect(mockedCreate).toHaveBeenLastCalledWith({
        test_session_id: "abc-123",
      }),
    );
  });

  it("renders suggested prompts for the current page context", async () => {
    primeHappyPath();
    renderOverlay();

    await userEvent.click(
      screen.getByRole("button", { name: "AI-советчик по химии" }),
    );

    expect(
      await screen.findByRole("button", { name: "Объясни кратко" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Проверь меня" }),
    ).toBeInTheDocument();
  });

  it("uses fullscreen dialog on mobile viewport classes", async () => {
    primeHappyPath();
    renderOverlay();

    await userEvent.click(
      screen.getByRole("button", { name: "AI-советчик по химии" }),
    );

    const dialog = await screen.findByRole("dialog", {
      name: "Чат AI-советчика",
    });
    expect(dialog.className).toContain("inset-0");
    expect(
      screen.getByRole("button", { name: "Закрыть чат" }),
    ).toBeInTheDocument();
  });
});
