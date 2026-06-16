import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CreateStudentForm } from "@/components/students/CreateStudentForm";
import { createStudent } from "@/lib/api/students";
import { ApiError } from "@/lib/api/client";

const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

vi.mock("@/lib/api/students", () => ({
  createStudent: vi.fn(),
}));

const mockedCreateStudent = vi.mocked(createStudent);

beforeEach(() => {
  vi.clearAllMocks();
});

async function fillAndSubmit() {
  await userEvent.type(screen.getByLabelText("Email"), "new@example.com");
  await userEvent.type(screen.getByLabelText("Временный пароль"), "secret1");
  await userEvent.selectOptions(screen.getByLabelText("Трек"), "oge");
  await userEvent.click(screen.getByRole("button", { name: "Создать ученика" }));
}

describe("CreateStudentForm", () => {
  it("creates a student and refreshes the page", async () => {
    mockedCreateStudent.mockResolvedValue({
      id: "1",
      email: "new@example.com",
      track: "oge",
      created_at: "2026-06-16T12:00:00Z",
    });

    render(<CreateStudentForm />);
    await fillAndSubmit();

    expect(mockedCreateStudent).toHaveBeenCalledWith({
      email: "new@example.com",
      password: "secret1",
      track: "oge",
    });
    expect(refresh).toHaveBeenCalled();
  });

  it("shows a friendly message on 409 conflict", async () => {
    mockedCreateStudent.mockRejectedValue(
      new ApiError(409, "Email already registered"),
    );

    render(<CreateStudentForm />);
    await fillAndSubmit();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Этот email уже зарегистрирован.",
    );
    expect(refresh).not.toHaveBeenCalled();
  });

  it("shows a friendly message on 403", async () => {
    mockedCreateStudent.mockRejectedValue(
      new ApiError(403, "Teacher role required"),
    );

    render(<CreateStudentForm />);
    await fillAndSubmit();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Недостаточно прав для создания ученика.",
    );
  });
});
