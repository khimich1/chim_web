import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { StudentNav } from "@/components/layout/StudentNav";

let pathname = "/student";

vi.mock("next/navigation", () => ({
  usePathname: () => pathname,
}));

describe("StudentNav", () => {
  it("renders brand and section links", () => {
    pathname = "/student";
    render(<StudentNav />);

    expect(screen.getByLabelText("Разделы кабинета ученика")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Главная" })).toHaveAttribute(
      "href",
      "/student",
    );
    expect(screen.getByRole("link", { name: "Учебник" })).toHaveAttribute(
      "href",
      "/student/textbook",
    );
    expect(screen.getByRole("link", { name: "Тесты" })).toHaveAttribute(
      "href",
      "/student/tests",
    );
    expect(screen.getByRole("link", { name: "Задания" })).toHaveAttribute(
      "href",
      "/student/homework",
    );
  });

  it("marks the active section with aria-current", () => {
    pathname = "/student/homework";
    render(<StudentNav />);

    expect(screen.getByRole("link", { name: "Задания" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Главная" })).not.toHaveAttribute(
      "aria-current",
    );
  });
});
