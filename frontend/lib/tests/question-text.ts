/** Inline formula wrapped in backticks (SPEC §14.4). */
const FORMULA_RE = /(`[^`]+`)/g;

export type TextSegment =
  | { kind: "text"; value: string }
  | { kind: "formula"; value: string };

/** Split plain question text into prose and formula chip segments. */
export function splitTextWithFormulas(text: string): TextSegment[] {
  const parts = text.split(FORMULA_RE).filter((part) => part.length > 0);

  return parts.map((part) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return { kind: "formula", value: part.slice(1, -1) };
    }
    return { kind: "text", value: part };
  });
}
