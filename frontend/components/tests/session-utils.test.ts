import { describe, expect, it } from "vitest";

import { formatSessionTitle, stepVerdict } from "@/components/tests/session-utils";
import type { TestSession, TestStep } from "@/lib/api/types";

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

function baseStep(overrides: Partial<TestStep>): TestStep {
  return {
    position: 0,
    test_id: 1,
    type: 1,
    question: "Q",
    options: null,
    status: "unseen",
    answer: null,
    is_correct: null,
    hint_used: false,
    ...overrides,
  };
}

describe("stepVerdict", () => {
  it("shows Засчитано for checked exam content self_check", () => {
    expect(
      stepVerdict(
        baseStep({
          type: 29,
          grading_mode: "self_check",
          status: "checked",
        }),
      ),
    ).toBe("✓ Засчитано");
  });

  it("shows Самопроверка for checked custom self_check", () => {
    expect(
      stepVerdict(
        baseStep({
          test_id: null,
          type: null,
          question: null,
          question_blocks: [{ type: "text", content: "Q" }],
          grading_mode: "self_check",
          status: "checked",
        }),
      ),
    ).toBe("Самопроверка");
  });
});
