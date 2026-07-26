import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CapturePage } from "@/components/homework/CapturePage";
import { ApiError } from "@/lib/api/client";
import { getMe } from "@/lib/api/auth";
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
const mockedGetMe = vi.mocked(getMe);

beforeEach(() => {
  vi.clearAllMocks();
  mockedGetMe.mockRejectedValue(new Error("unauthenticated"));
  vi.stubGlobal("URL", {
    ...URL,
    createObjectURL: vi.fn(() => "blob:preview"),
    revokeObjectURL: vi.fn(),
  });
  mockedMeta.mockResolvedValue({
    purpose: "answer",
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
    expect(screen.getByText("Съёмка решения")).toBeInTheDocument();
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
      purpose: "answer",
      position: 0,
      answer_image_ids: ["img-1"],
      answer_image_urls: ["/api/uploads/images/img-1"],
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
    expect(screen.getByText(/Сравнить ответ/)).toBeInTheDocument();
  });

  it("on 401 for feedback capture shows login with redirect, not fatal invalid token", async () => {
    mockedMeta.mockRejectedValue(new ApiError(401, "Not authenticated"));

    render(<CapturePage token="tok-fb-unauth" />);

    expect(await screen.findByText("Съёмка разбора")).toBeInTheDocument();
    expect(
      screen.getByText(/войдите как преподаватель/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Войти" }),
    ).toHaveAttribute("href", "/login?redirect=/student/capture/tok-fb-unauth");
    expect(
      screen.queryByText(/недействительна/i),
    ).not.toBeInTheDocument();

    const fileInput = screen.getByLabelText(
      /Сфотографировать или выбрать файл/i,
    );
    expect(fileInput).toBeDisabled();
    expect(screen.getByRole("button", { name: "Отправить фото" })).toBeDisabled();
  });

  it("disables feedback intake until authenticated even when meta loads", async () => {
    mockedMeta.mockResolvedValue({
      purpose: "feedback",
      homework_id: "hw-1",
      position: 0,
      task_title: "Фото к разбору",
      question_preview: "Сфотографируйте пояснение к разбору",
      expires_at: "2026-07-25T12:00:00Z",
      already_has_photo: false,
      staged_image_id: null,
      staged_image_url: null,
    });

    render(<CapturePage token="tok-fb" />);

    expect(await screen.findByText("Съёмка разбора")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Войти" }),
    ).toHaveAttribute("href", "/login?redirect=/student/capture/tok-fb");

    for (const label of ["Весь лист в кадре", "Хорошее освещение", "Без размытия"]) {
      await userEvent.click(screen.getByLabelText(label));
    }

    expect(
      screen.getByLabelText(/Сфотографировать или выбрать файл/i),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: "Отправить фото" })).toBeDisabled();
    expect(mockedUpload).not.toHaveBeenCalled();
  });

  it("shows feedback copy and accepts staged upload when authenticated", async () => {
    mockedGetMe.mockResolvedValue({
      id: "t1",
      email: "teacher@example.com",
      role: "teacher",
      track: null,
    });
    mockedMeta.mockResolvedValue({
      purpose: "feedback",
      homework_id: "hw-1",
      position: 0,
      task_title: "Фото к разбору",
      question_preview: "Сфотографируйте пояснение к разбору",
      expires_at: "2026-07-25T12:00:00Z",
      already_has_photo: false,
      staged_image_id: null,
      staged_image_url: null,
    });
    mockedUpload.mockResolvedValue({
      purpose: "feedback",
      position: 0,
      staged_image_id: "staged-1",
      staged_image_url: "/api/uploads/images/staged-1",
    });

    render(<CapturePage token="tok-fb" />);

    expect(await screen.findByText("Съёмка разбора")).toBeInTheDocument();
    expect(
      screen.getByText("Сфотографируйте пояснение к разбору"),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/войдите как преподаватель/i),
    ).not.toBeInTheDocument();

    for (const label of ["Весь лист в кадре", "Хорошее освещение", "Без размытия"]) {
      await userEvent.click(screen.getByLabelText(label));
    }
    await userEvent.upload(
      screen.getByLabelText(/Сфотографировать или выбрать файл/i),
      new File(["photo"], "fb.jpg", { type: "image/jpeg" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Отправить фото" }));

    expect(await screen.findByText("Фото отправлено")).toBeInTheDocument();
    expect(screen.getByText(/форме разбора/i)).toBeInTheDocument();
    expect(screen.queryByText(/Сравнить ответ/)).not.toBeInTheDocument();
  });
});
