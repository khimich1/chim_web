import { describe, expect, it } from "vitest";

import {
  countsTowardScore,
  isCustomSelfCheck,
  isExamContentSelfCheck,
} from "@/lib/tests/grading-utils";
import type { TestStep } from "@/lib/api/types";

function step(overrides: Partial<TestStep>): TestStep {
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

describe("grading-utils", () => {
  it("detects exam content self_check (EGE types 29–34)", () => {
    const examStep = step({
      type: 29,
      grading_mode: "self_check",
    });

    expect(isExamContentSelfCheck(examStep)).toBe(true);
    expect(isCustomSelfCheck(examStep)).toBe(false);
    expect(countsTowardScore(examStep)).toBe(true);
  });

  it("detects custom self_check excluded from score", () => {
    const customStep = step({
      test_id: null,
      type: null,
      question: null,
      question_blocks: [{ type: "text", content: "Q" }],
      grading_mode: "self_check",
    });

    expect(isCustomSelfCheck(customStep)).toBe(true);
    expect(isExamContentSelfCheck(customStep)).toBe(false);
    expect(countsTowardScore(customStep)).toBe(false);
  });

  it("counts exact exam steps toward score", () => {
    const exactStep = step({ grading_mode: undefined });

    expect(countsTowardScore(exactStep)).toBe(true);
  });
});
