import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { LoginForm } from "@/components/auth/LoginForm";
import { login } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";

const replace = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, refresh }),
}));

vi.mock("@/lib/api/auth", () => ({
  login: vi.fn(),
}));

const mockedLogin = vi.mocked(login);

beforeEach(() => {
  vi.clearAllMocks();
});

async function fillAndSubmit(email: string, password: string) {
  await userEvent.type(screen.getByLabelText("Email"), email);
  await userEvent.type(screen.getByLabelText("Пароль"), password);
  await userEvent.click(screen.getByRole("button", { name: "Войти" }));
}

describe("LoginForm", () => {
  it("logs in a teacher and redirects to /teacher", async () => {
    mockedLogin.mockResolvedValue({
      id: "1",
      email: "teacher@example.com",
      role: "teacher",
      track: null,
    });

    render(<LoginForm />);
    await fillAndSubmit("teacher@example.com", "pw");

    expect(mockedLogin).toHaveBeenCalledWith("teacher@example.com", "pw");
    expect(replace).toHaveBeenCalledWith("/teacher");
  });

  it("redirects a student to /student", async () => {
    mockedLogin.mockResolvedValue({
      id: "2",
      email: "student@example.com",
      role: "student",
      track: "oge",
    });

    render(<LoginForm />);
    await fillAndSubmit("student@example.com", "pw");

    expect(replace).toHaveBeenCalledWith("/student");
  });

  it("shows an error and does not redirect on 401", async () => {
    mockedLogin.mockRejectedValue(new ApiError(401, "Invalid email or password"));

    render(<LoginForm />);
    await fillAndSubmit("teacher@example.com", "wrong");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Неверный email или пароль",
    );
    expect(replace).not.toHaveBeenCalled();
  });
});
