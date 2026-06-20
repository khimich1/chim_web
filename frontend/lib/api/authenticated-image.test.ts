import { describe, expect, it } from "vitest";

import { resolveImagePath } from "@/lib/api/authenticated-image";

describe("resolveImagePath", () => {
  it("returns relative paths unchanged", () => {
    expect(resolveImagePath("/api/uploads/images/abc")).toBe(
      "/api/uploads/images/abc",
    );
  });

  it("extracts pathname from absolute API URL", () => {
    expect(
      resolveImagePath("http://localhost:8000/api/uploads/images/abc"),
    ).toBe("/api/uploads/images/abc");
  });
});
