import {
  createEvent,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { ContentBlocksEditor } from "@/components/teacher/ContentBlocksEditor";
import { uploadImage } from "@/lib/api/uploads";
import type { ContentBlock } from "@/lib/api/types";
import { IMAGE_INTAKE_HINT } from "@/lib/image-intake";

vi.mock("@/lib/api/uploads", () => ({
  uploadImage: vi.fn(),
}));

vi.mock("@/components/common/AuthenticatedImage", () => ({
  AuthenticatedImage: ({
    src,
    alt,
    className,
  }: {
    src: string;
    alt: string;
    className?: string;
  }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} className={className} data-testid="auth-image" />
  ),
}));

const mockedUpload = vi.mocked(uploadImage);

function makeImageFile(name: string, type = "image/png"): File {
  return new File(["img"], name, { type });
}

function clipboardDataFor(files: File[]) {
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
  };
}

function dataTransferFor(files: File[]) {
  return clipboardDataFor(files);
}

describe("ContentBlocksEditor image intake", () => {
  beforeEach(() => {
    mockedUpload.mockReset();
  });

  it("shows paste/DnD hint", () => {
    render(
      <ContentBlocksEditor
        blocks={[]}
        onChange={vi.fn()}
        label="Вопрос"
      />,
    );

    expect(screen.getByText(IMAGE_INTAKE_HINT)).toBeInTheDocument();
  });

  it("pastes an image and appends an image block", async () => {
    const onChange = vi.fn();
    mockedUpload.mockResolvedValue({
      id: "img-1",
      url: "/api/uploads/images/img-1",
    });

    render(
      <ContentBlocksEditor
        blocks={[{ type: "text", content: "Hello" }]}
        onChange={onChange}
        label="Вопрос"
      />,
    );

    const zone = screen.getByTestId("content-blocks-intake");
    const event = createEvent.paste(zone, {
      clipboardData: clipboardDataFor([makeImageFile("shot.png")]),
    });
    const preventDefault = vi.spyOn(event, "preventDefault");
    fireEvent(zone, event);

    await waitFor(() => {
      expect(mockedUpload).toHaveBeenCalledTimes(1);
      expect(onChange).toHaveBeenCalledWith([
        { type: "text", content: "Hello" },
        { type: "image", url: "/api/uploads/images/img-1" },
      ]);
    });

    expect(preventDefault).toHaveBeenCalled();
  });

  it("does not preventDefault on text-only paste", () => {
    const onChange = vi.fn();

    render(
      <ContentBlocksEditor
        blocks={[{ type: "text", content: "" }]}
        onChange={onChange}
        label="Вопрос"
      />,
    );

    const zone = screen.getByTestId("content-blocks-intake");
    const preventDefault = vi.fn();
    fireEvent.paste(zone, {
      clipboardData: {
        items: {
          length: 0,
          [Symbol.iterator]: function* () {},
        },
        files: {
          length: 0,
          item: () => null,
          [Symbol.iterator]: function* () {},
        },
        getData: () => "plain text",
      },
      preventDefault,
    });

    expect(preventDefault).not.toHaveBeenCalled();
    expect(mockedUpload).not.toHaveBeenCalled();
    expect(onChange).not.toHaveBeenCalled();
  });

  it("inserts image after the focused textarea block", async () => {
    const onChange = vi.fn();
    mockedUpload.mockResolvedValue({
      id: "img-2",
      url: "/api/uploads/images/img-2",
    });

    const blocks: ContentBlock[] = [
      { type: "text", content: "A" },
      { type: "text", content: "B" },
      { type: "text", content: "C" },
    ];

    render(
      <ContentBlocksEditor blocks={blocks} onChange={onChange} label="Вопрос" />,
    );

    const textareas = screen.getAllByPlaceholderText("Текст задания…");
    fireEvent.focus(textareas[0]!);

    const zone = screen.getByTestId("content-blocks-intake");
    fireEvent.paste(zone, {
      clipboardData: clipboardDataFor([makeImageFile("after-a.png")]),
    });

    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith([
        { type: "text", content: "A" },
        { type: "image", url: "/api/uploads/images/img-2" },
        { type: "text", content: "B" },
        { type: "text", content: "C" },
      ]);
    });
  });

  it("drops multiple images up to 10 and reports truncation", async () => {
    const onChange = vi.fn();
    mockedUpload.mockImplementation(async (file: File) => ({
      id: `id-${file.name}`,
      url: `/api/uploads/images/${file.name}`,
    }));

    render(
      <ContentBlocksEditor blocks={[]} onChange={onChange} label="Вопрос" />,
    );

    const files = Array.from({ length: 11 }, (_, i) =>
      makeImageFile(`${i}.png`),
    );
    const zone = screen.getByTestId("content-blocks-intake");
    fireEvent.drop(zone, {
      dataTransfer: dataTransferFor(files),
    });

    await waitFor(() => {
      expect(mockedUpload).toHaveBeenCalledTimes(10);
    });

    expect(
      screen.getByText(/за раз можно загрузить не более 10/i),
    ).toBeInTheDocument();

    const lastCall = onChange.mock.calls.at(-1)?.[0] as ContentBlock[];
    expect(lastCall).toHaveLength(10);
    expect(lastCall.every((b) => b.type === "image")).toBe(true);
  });

  it("renders image preview with test-style classes via AuthenticatedImage", () => {
    render(
      <ContentBlocksEditor
        blocks={[{ type: "image", url: "/api/uploads/images/x" }]}
        onChange={vi.fn()}
        label="Вопрос"
      />,
    );

    const img = screen.getByTestId("auth-image");
    expect(img).toHaveClass("max-w-full");
    expect(img).toHaveClass("object-contain");
  });
});
