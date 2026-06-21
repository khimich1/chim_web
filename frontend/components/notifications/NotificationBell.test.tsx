import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { NotificationBell } from "@/components/notifications/NotificationBell";
import type { Notification } from "@/lib/api/types";

const push = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh }),
}));

vi.mock("@/lib/api/notifications", () => ({
  getUnreadCount: vi.fn().mockResolvedValue({ count: 0 }),
  markNotificationRead: vi.fn(),
}));

const notifications: Notification[] = [
  {
    id: "n-1",
    type: "homework_submitted",
    payload: {
      homework_id: "hw-1",
      homework_title: "Алканы",
      student_id: "student-1",
      student_email: "student@example.com",
      answered_steps: 1,
      total_steps: 2,
      completion_percent: 50,
    },
    read_at: null,
    created_at: "2026-01-01T12:00:00Z",
  },
];

describe("NotificationBell", () => {
  it("shows partial homework progress in dropdown", async () => {
    const user = userEvent.setup();

    render(
      <NotificationBell initialNotifications={notifications} initialUnread={1} />,
    );

    await user.click(screen.getByRole("button", { name: /Уведомления/ }));

    expect(
      screen.getByText("student@example.com сдал(а) «Алканы» (1/2, 50%)"),
    ).toBeInTheDocument();
  });
});
