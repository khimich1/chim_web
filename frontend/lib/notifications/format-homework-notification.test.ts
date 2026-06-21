import { describe, expect, it } from "vitest";

import { formatHomeworkSubmittedNotification } from "@/lib/notifications/format-homework-notification";

const basePayload = {
  homework_id: "hw-1",
  homework_title: "Алканы",
  student_id: "student-1",
  student_email: "student@example.com",
};

describe("formatHomeworkSubmittedNotification", () => {
  it("includes partial progress when payload has step counts", () => {
    expect(
      formatHomeworkSubmittedNotification({
        ...basePayload,
        answered_steps: 1,
        total_steps: 2,
        completion_percent: 50,
      }),
    ).toBe("student@example.com сдал(а) «Алканы» (1/2, 50%)");
  });

  it("includes full progress when completion is 100%", () => {
    expect(
      formatHomeworkSubmittedNotification({
        ...basePayload,
        answered_steps: 2,
        total_steps: 2,
        completion_percent: 100,
      }),
    ).toBe("student@example.com сдал(а) «Алканы» (2/2, 100%)");
  });

  it("falls back to base message without progress fields", () => {
    expect(formatHomeworkSubmittedNotification(basePayload)).toBe(
      "student@example.com сдал(а) «Алканы»",
    );
  });
});
