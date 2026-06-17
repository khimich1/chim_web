import { describe, expect, it } from "vitest";

import { formatFetchError, ApiError } from "@/lib/api/client";

describe("formatFetchError", () => {
  it("returns ApiError message for HTTP errors", () => {
    expect(formatFetchError(new ApiError(401, "Invalid"), "fallback")).toBe(
      "Invalid",
    );
  });

  it("maps Failed to fetch to unreachable backend message", () => {
    expect(
      formatFetchError(new TypeError("Failed to fetch"), "fallback"),
    ).toContain("Бэкенд не отвечает на");
    expect(
      formatFetchError(new TypeError("Failed to fetch"), "fallback"),
    ).toContain("localhost:8000");
  });

  it("maps timeout errors to timeout message", () => {
    const err = new DOMException("The operation timed out.", "TimeoutError");
    expect(formatFetchError(err, "fallback")).toContain(
      "Превышено время ожидания API",
    );
  });

  it("maps AbortError to timeout message", () => {
    const err = new DOMException("Aborted", "AbortError");
    expect(formatFetchError(err, "fallback")).toContain(
      "Превышено время ожидания API",
    );
  });

  it("returns fallback for unknown errors", () => {
    expect(formatFetchError("oops", "fallback")).toBe("fallback");
  });
});
