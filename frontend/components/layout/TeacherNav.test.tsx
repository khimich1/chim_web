import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { TeacherNav } from "@/components/layout/TeacherNav";

let pathname = "/teacher";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn(), replace: vi.fn() }),
  usePathname: () => pathname,
}));

vi.mock("@/lib/api/notifications", () => ({
  getUnreadCount: vi.fn().mockResolvedValue({ count: 0 }),
  markNotificationRead: vi.fn(),
}));

vi.mock("@/lib/api/auth", () => ({
  logout: vi.fn(),
}));

const navProps = {
  initialNotifications: [],
  initialUnread: 0,
};

describe("TeacherNav", () => {
  it("renders brand, section links, bell, and logout", () => {
    pathname = "/teacher";
    render(<TeacherNav {...navProps} />);

    expect(screen.getByLabelText("Разделы кабинета преподавателя")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Главная" })).toHaveAttribute(
      "href",
      "/teacher",
    );
    expect(screen.getByRole("link", { name: "Ученики" })).toHaveAttribute(
      "href",
      "/teacher/students",
    );
    expect(
      screen.getByRole("link", { name: "Конструктор заданий" }),
    ).toHaveAttribute("href", "/teacher/themes");
    expect(screen.getByRole("link", { name: "Конструктор заданий" })).toHaveTextContent(
      "Конструктор",
    );
    expect(screen.getByRole("link", { name: "Задания" })).toHaveAttribute(
      "href",
      "/teacher/homework",
    );
    expect(screen.getByRole("link", { name: "Уведомления" })).toHaveAttribute(
      "href",
      "/teacher/notifications",
    );
    expect(screen.getByRole("button", { name: "Уведомления" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Выйти" })).toBeInTheDocument();
  });

  it("marks the active section with aria-current", () => {
    pathname = "/teacher/homework/new";
    render(<TeacherNav {...navProps} />);

    expect(screen.getByRole("link", { name: "Задания" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Главная" })).not.toHaveAttribute(
      "aria-current",
    );
  });

  it("centers the section nav between brand and actions", () => {
    pathname = "/teacher";
    const { container } = render(<TeacherNav {...navProps} />);

    const headerRow = container.querySelector("header > div");
    expect(headerRow).toBeTruthy();

    const brandSlot = headerRow!.children[0] as HTMLElement;
    const nav = screen.getByLabelText("Разделы кабинета преподавателя");
    const actionsSlot = headerRow!.children[2] as HTMLElement;

    expect(brandSlot.className).toMatch(/flex-1/);
    expect(actionsSlot.className).toMatch(/flex-1/);
    expect(actionsSlot.className).toMatch(/justify-end/);
    expect(nav.className).not.toMatch(/flex-1/);
    expect(nav.querySelector("ul")?.className).toMatch(/justify-center/);
  });
});
