import { describe, expect, it } from "vitest";

import { formatSessionTitle } from "@/components/tests/session-utils";
import type { TestSession } from "@/lib/api/types";

function baseSession(overrides: Partial<TestSession>): TestSession {
  return {
    id: "sess-1",
    track: "ege",
    variant_ref: "001.txt",
    homework_assignment_id: null,
    status: "in_progress",
    score: null,
    max_score: null,
    total_steps: 1,
    steps: [],
    ...overrides,
  };
}

describe("formatSessionTitle", () => {
  it("formats a single-variant session", () => {
    expect(formatSessionTitle(baseSession({ variant_ref: "003.txt" }))).toBe(
      "Вариант 003",
    );
  });

  it("returns homework label when variant_ref is null", () => {
    expect(
      formatSessionTitle(
        baseSession({
          variant_ref: null,
          homework_assignment_id: "hw-1",
        }),
      ),
    ).toBe("Домашнее задание");
  });

  it("returns custom theme label", () => {
    expect(
      formatSessionTitle(
        baseSession({
          variant_ref: null,
          custom_theme_id: "theme-1",
          source: "custom",
        }),
      ),
    ).toBe("Авторская тема");
  });

  it("returns mixed-session fallback when both refs are null", () => {
    expect(
      formatSessionTitle(
        baseSession({
          variant_ref: null,
          homework_assignment_id: null,
        }),
      ),
    ).toBe("Смешанная сессия");
  });
});
