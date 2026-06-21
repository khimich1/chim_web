import { describe, expect, it } from "vitest";

import { formatHomeworkSubmissionProgress } from "@/lib/homework/format-submission-progress";

describe("formatHomeworkSubmissionProgress", () => {
  it("returns progress suffix when steps are present", () => {
    expect(
      formatHomeworkSubmissionProgress({
        answered_steps: 1,
        total_steps: 2,
        completion_percent: 50,
      }),
    ).toBe(" (1/2, 50%)");
  });

  it("defaults completion percent to 0 when missing", () => {
    expect(
      formatHomeworkSubmissionProgress({
        answered_steps: 1,
        total_steps: 2,
        completion_percent: null,
      }),
    ).toBe(" (1/2, 0%)");
  });

  it("returns empty string without progress fields", () => {
    expect(formatHomeworkSubmissionProgress(null)).toBe("");
    expect(formatHomeworkSubmissionProgress({})).toBe("");
  });
});
