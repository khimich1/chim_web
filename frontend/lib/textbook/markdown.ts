/**
 * Textbook lecture markdown preprocessing (SPEC §14.4).
 *
 * Decision: content DB is read-only — map known emoji markers to callout types
 * at render time instead of mutating stored lectures.
 *
 * XSS: strip raw HTML / script patterns before parsing; ReactMarkdown is used
 * without rehype-raw so only safe markdown nodes reach the DOM.
 */

export type CalloutVariant = "important" | "example" | "remember";

/** Known emoji markers → callout variant (SPEC §14.4). */
export const CALLOUT_EMOJI_MAP: Readonly<
  Record<string, { variant: CalloutVariant; label: string }>
> = {
  "\u{1F4CC}": { variant: "important", label: "\u0412\u0430\u0436\u043d\u043e" }, // 📌
  "\u{1F4A1}": { variant: "example", label: "\u041f\u0440\u0438\u043c\u0435\u0440" }, // 💡
  "\u{1F680}": { variant: "remember", label: "\u0417\u0430\u043f\u043e\u043c\u043d\u0438" }, // 🚀
};

export type LectureSegment =
  | { type: "markdown"; content: string }
  | { type: "callout"; variant: CalloutVariant; content: string };

const CALLOUT_PREFIX = new RegExp(
  `^\\s*(${Object.keys(CALLOUT_EMOJI_MAP).join("|")})\\s*`,
  "u",
);

/** Remove dangerous HTML / URI patterns from lecture text (defense in depth). */
export function sanitizeLectureText(text: string): string {
  return text
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "")
    .replace(/on\w+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, "")
    .replace(/javascript:/gi, "")
    .replace(/<[^>]+>/g, "");
}

function detectCallout(line: string): {
  variant: CalloutVariant;
  content: string;
} | null {
  const match = line.match(CALLOUT_PREFIX);
  if (!match) {
    return null;
  }
  const mapping = CALLOUT_EMOJI_MAP[match[1]];
  if (!mapping) {
    return null;
  }
  const content = line.slice(match[0].length).trim();
  return { variant: mapping.variant, content };
}

/**
 * Split lecture markdown into plain segments and callout blocks.
 * Consecutive callout lines of the same type are merged.
 */
export function parseLectureSegments(markdown: string): LectureSegment[] {
  const safe = sanitizeLectureText(markdown);
  const lines = safe.split("\n");
  const segments: LectureSegment[] = [];
  let buffer: string[] = [];
  let calloutBuffer: { variant: CalloutVariant; lines: string[] } | null =
    null;

  function flushMarkdown() {
    if (buffer.length > 0) {
      const content = buffer.join("\n").trim();
      if (content) {
        segments.push({ type: "markdown", content });
      }
      buffer = [];
    }
  }

  function flushCallout() {
    if (calloutBuffer && calloutBuffer.lines.length > 0) {
      const content = calloutBuffer.lines.join("\n").trim();
      if (content) {
        segments.push({
          type: "callout",
          variant: calloutBuffer.variant,
          content,
        });
      }
    }
    calloutBuffer = null;
  }

  for (const line of lines) {
    const callout = detectCallout(line);
    if (callout) {
      flushMarkdown();
      if (
        calloutBuffer &&
        calloutBuffer.variant === callout.variant
      ) {
        calloutBuffer.lines.push(callout.content);
      } else {
        flushCallout();
        calloutBuffer = { variant: callout.variant, lines: [callout.content] };
      }
      continue;
    }

    flushCallout();
    buffer.push(line);
  }

  flushCallout();
  flushMarkdown();

  if (segments.length === 0 && safe.trim()) {
    segments.push({ type: "markdown", content: safe.trim() });
  }

  return segments;
}
