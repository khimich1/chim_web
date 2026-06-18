import { describe, expect, it } from "vitest";

import { getSuggestedPrompts } from "@/lib/tutor/suggestedPrompts";

describe("getSuggestedPrompts", () => {
  it("returns theory prompts on a test session page", () => {
    const prompts = getSuggestedPrompts({ test_session_id: "abc-123" });
    expect(prompts.map((item) => item.label)).toEqual([
      "Подскажи теорию",
      "Объясни кратко",
    ]);
  });

  it("returns topic prompts on a textbook page", () => {
    const prompts = getSuggestedPrompts({ topic: "Алканы" });
    expect(prompts.map((item) => item.label)).toEqual([
      "Объясни кратко",
      "Проверь меня",
    ]);
    expect(prompts[0]?.message).toContain("Алканы");
  });

  it("returns a homework prompt when homework context is set", () => {
    const prompts = getSuggestedPrompts({ homework_id: "hw-1" });
    expect(prompts[0]?.label).toBe("Что задано?");
  });
});
