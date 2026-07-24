import { describe, expect, it } from "vitest";

import {
  CONTENT_IMAGE_CLASS,
  imageFilesFromDataTransfer,
  isAllowedImageFile,
  isAllowedImageMime,
} from "@/lib/image-intake";

function makeFile(name: string, type: string): File {
  return new File(["x"], name, { type });
}

function mockDataTransfer(files: File[]): DataTransfer {
  const items = files.map((file) => ({
    kind: "file" as const,
    type: file.type,
    getAsFile: () => file,
  }));

  return {
    items: {
      length: items.length,
      ...items,
      [Symbol.iterator]: function* () {
        yield* items;
      },
    },
    files: {
      length: files.length,
      ...files,
      item: (index: number) => files[index] ?? null,
      [Symbol.iterator]: function* () {
        yield* files;
      },
    },
  } as unknown as DataTransfer;
}

describe("isAllowedImageMime", () => {
  it("allows jpeg, png, and webp", () => {
    expect(isAllowedImageMime("image/jpeg")).toBe(true);
    expect(isAllowedImageMime("image/png")).toBe(true);
    expect(isAllowedImageMime("image/webp")).toBe(true);
  });

  it("rejects gif, pdf, and empty", () => {
    expect(isAllowedImageMime("image/gif")).toBe(false);
    expect(isAllowedImageMime("application/pdf")).toBe(false);
    expect(isAllowedImageMime("")).toBe(false);
  });
});

describe("isAllowedImageFile", () => {
  it("returns true for allowed MIME types", () => {
    expect(isAllowedImageFile(makeFile("a.png", "image/png"))).toBe(true);
  });

  it("returns false for disallowed MIME types", () => {
    expect(isAllowedImageFile(makeFile("a.gif", "image/gif"))).toBe(false);
  });
});

describe("imageFilesFromDataTransfer", () => {
  it("returns empty files when dataTransfer is null", () => {
    expect(imageFilesFromDataTransfer(null, { limit: 10 })).toEqual({
      files: [],
      truncated: false,
    });
  });

  it("returns empty files when no images present", () => {
    const dt = mockDataTransfer([makeFile("doc.pdf", "application/pdf")]);
    expect(imageFilesFromDataTransfer(dt, { limit: 10 })).toEqual({
      files: [],
      truncated: false,
    });
  });

  it("filters to allowed images and preserves order", () => {
    const png = makeFile("a.png", "image/png");
    const gif = makeFile("b.gif", "image/gif");
    const jpeg = makeFile("c.jpg", "image/jpeg");
    const dt = mockDataTransfer([png, gif, jpeg]);

    expect(imageFilesFromDataTransfer(dt, { limit: 10 })).toEqual({
      files: [png, jpeg],
      truncated: false,
    });
  });

  it("truncates to limit and sets truncated flag", () => {
    const files = [
      makeFile("1.png", "image/png"),
      makeFile("2.png", "image/png"),
      makeFile("3.png", "image/png"),
    ];
    const dt = mockDataTransfer(files);

    expect(imageFilesFromDataTransfer(dt, { limit: 2 })).toEqual({
      files: [files[0], files[1]],
      truncated: true,
    });
  });

  it("returns all files when count equals limit", () => {
    const files = [
      makeFile("1.webp", "image/webp"),
      makeFile("2.webp", "image/webp"),
    ];
    const dt = mockDataTransfer(files);

    expect(imageFilesFromDataTransfer(dt, { limit: 2 })).toEqual({
      files,
      truncated: false,
    });
  });
});

describe("CONTENT_IMAGE_CLASS", () => {
  it("matches the test-style display classes", () => {
    expect(CONTENT_IMAGE_CLASS).toContain("max-w-full");
    expect(CONTENT_IMAGE_CLASS).toContain("object-contain");
  });
});
