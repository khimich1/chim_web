import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CapturePage } from "@/components/homework/CapturePage";
import { captureUpload, getCaptureMeta } from "@/lib/api/handoff";

vi.mock("@/lib/api/handoff", () => ({
  getCaptureMeta: vi.fn(),
  captureUpload: vi.fn(),
}));

vi.mock("@/lib/api/auth", () => ({
  getMe: vi.fn().mockRejectedValue(new Error("unauthenticated")),
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

const mockedMeta = vi.mocked(getCaptureMeta);
const mockedUpload = vi.mocked(captureUpload);

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("URL", {
    ...URL,
    createObjectURL: vi.fn(() => "blob:preview"),
    revokeObjectURL: vi.fn(),
  });
  mockedMeta.mockResolvedValue({
    session_id: "sess-1",
    position: 0,
    task_title: "Self check",
    question_preview: "Explain reaction",
    expires_at: "2026-06-20T12:00:00Z",
    already_has_photo: false,
  });
});

describe("CapturePage", () => {
  it("shows checklist and blocks camera until complete", async () => {
    render(<CapturePage token="token-1" />);

    expect(await screen.findByText("Explain reaction")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Чеклист перед съёмкой"),
    ).toBeInTheDocument();

    const fileInput = screen.getByLabelText(
      /Сфотографировать или выбрать файл/i,
    );
    expect(fileInput).toBeDisabled();

    await userEvent.click(screen.getByLabelText("Весь лист в кадре"));
    await userEvent.click(screen.getByLabelText("Хорошее освещение"));
    await userEvent.click(screen.getByLabelText("Без размытия"));

    expect(fileInput).not.toBeDisabled();
  });

  it("submits photo after preview", async () => {
    mockedUpload.mockResolvedValue({
      position: 0,
      answer_image_id: "img-1",
      answer_image_url: "/api/uploads/images/img-1",
    });

    render(<CapturePage token="token-1" />);
    await screen.findByText("Explain reaction");

    for (const label of ["Весь лист в кадре", "Хорошее освещение", "Без размытия"]) {
      await userEvent.click(screen.getByLabelText(label));
    }

    const file = new File(["photo"], "work.jpg", { type: "image/jpeg" });
    await userEvent.upload(
      screen.getByLabelText(/Сфотографировать или выбрать файл/i),
      file,
    );

    await userEvent.click(screen.getByRole("button", { name: "Отправить фото" }));

    await waitFor(() => {
      expect(mockedUpload).toHaveBeenCalledWith("token-1", expect.any(File));
    });
    expect(await screen.findByText("Фото отправлено")).toBeInTheDocument();
  });
});
