import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { VariantPicker } from "@/components/tests/VariantPicker";
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

const variants = [{ filename: "001.txt" }, { filename: "002.txt" }];

beforeEach(() => {
  vi.clearAllMocks();
  mockedActive.mockResolvedValue({ session_id: null });
});

describe("VariantPicker", () => {
  it("shows continue for variants with active sessions", async () => {
    mockedActive.mockImplementation(async ({ variantRef }) => ({
      session_id: variantRef === "001.txt" ? "sess-1" : null,
    }));

    render(<VariantPicker variants={variants} />);

    expect(await screen.findByRole("button", { name: "Продолжить" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Начать" })).toBeInTheDocument();
  });

  it("navigates to active session on continue", async () => {
    mockedActive.mockResolvedValue({ session_id: "sess-1" });

    render(<VariantPicker variants={[variants[0]]} />);

    await userEvent.click(await screen.findByRole("button", { name: "Продолжить" }));
    expect(push).toHaveBeenCalledWith("/student/tests/sessions/sess-1");
    expect(mockedCreate).not.toHaveBeenCalled();
  });

  it("starts a new session when none is active", async () => {
    mockedCreate.mockResolvedValue({
      id: "sess-new",
      track: "ege",
      variant_ref: "002.txt",
      homework_assignment_id: null,
      status: "in_progress",
      score: null,
      max_score: null,
      total_steps: 34,
      steps: [],
    });

    render(<VariantPicker variants={[variants[1]]} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Начать" })).toBeEnabled();
    });

    await userEvent.click(screen.getByRole("button", { name: "Начать" }));

    expect(mockedCreate).toHaveBeenCalledWith("002.txt");
    expect(push).toHaveBeenCalledWith("/student/tests/sessions/sess-new");
  });
});
