import { describe, expect, it } from "vitest";

import {
  CALLOUT_EMOJI_MAP,
  parseLectureSegments,
  sanitizeLectureText,
} from "@/lib/textbook/markdown";

describe("sanitizeLectureText", () => {
  it("strips script tags and inline handlers", () => {
    const dirty =
      '<script>alert(1)</script>Текст <img onerror="x" src="x"> javascript:alert(1)';
    expect(sanitizeLectureText(dirty)).toBe("Текст  alert(1)");
  });
});

describe("parseLectureSegments", () => {
  it("maps emoji markers to callout segments (SPEC §14.4)", () => {
    const lecture = [
      "# Заголовок",
      "",
      "📌 Ионы важны.",
      "💡 Например, NaCl.",
    ].join("\n");

    const segments = parseLectureSegments(lecture);

    expect(segments).toEqual([
      { type: "markdown", content: "# Заголовок" },
      { type: "callout", variant: "important", content: "Ионы важны." },
      { type: "callout", variant: "example", content: "Например, NaCl." },
    ]);
  });

  it("documents emoji mapping labels", () => {
    expect(CALLOUT_EMOJI_MAP["\u{1F4CC}"].label).toBe("Важно");
    expect(CALLOUT_EMOJI_MAP["\u{1F4A1}"].label).toBe("Пример");
  });
});
