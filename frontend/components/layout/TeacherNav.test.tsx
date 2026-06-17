import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { TeacherNav } from "@/components/layout/TeacherNav";

let pathname = "/teacher";

vi.mock("next/navigation", () => ({
  usePathname: () => pathname,
}));

describe("TeacherNav", () => {
  it("renders brand and section links", () => {
    pathname = "/teacher";
    render(<TeacherNav />);

    expect(screen.getByLabelText("Разделы кабинета преподавателя")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Главная" })).toHaveAttribute(
      "href",
      "/teacher",
    );
    expect(screen.getByRole("link", { name: "Ученики" })).toHaveAttribute(
      "href",
      "/teacher/students",
    );
    expect(screen.getByRole("link", { name: "Задания" })).toHaveAttribute(
      "href",
      "/teacher/homework",
    );
    expect(screen.getByRole("link", { name: "Уведомления" })).toHaveAttribute(
      "href",
      "/teacher/notifications",
    );
  });

  it("marks the active section with aria-current", () => {
    pathname = "/teacher/homework/new";
    render(<TeacherNav />);

    expect(screen.getByRole("link", { name: "Задания" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Главная" })).not.toHaveAttribute(
      "aria-current",
    );
  });
});
