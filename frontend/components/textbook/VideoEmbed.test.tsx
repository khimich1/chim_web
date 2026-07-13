import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { parseVideoEmbedUrl, VideoEmbed } from "@/components/textbook/VideoEmbed";

describe("parseVideoEmbedUrl", () => {
  it("converts YouTube watch URLs to embed URLs", () => {
    expect(
      parseVideoEmbedUrl("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    ).toBe("https://www.youtube.com/embed/dQw4w9WgXcQ");
  });

  it("converts youtu.be URLs to embed URLs", () => {
    expect(parseVideoEmbedUrl("https://youtu.be/abc123XYZ")).toBe(
      "https://www.youtube.com/embed/abc123XYZ",
    );
  });

  it("converts VK video URLs to video_ext embed URLs", () => {
    expect(parseVideoEmbedUrl("https://vk.com/video-123456_789")).toBe(
      "https://vk.com/video_ext.php?oid=-123456&id=789&hd=2",
    );
  });

  it("rejects untrusted hosts", () => {
    expect(parseVideoEmbedUrl("https://evil.example.com/video")).toBeNull();
  });
});

describe("VideoEmbed", () => {
  it("renders sandboxed iframe for allowed YouTube URL", () => {
    render(
      <VideoEmbed videoUrl="https://www.youtube.com/watch?v=dQw4w9WgXcQ" />,
    );

    const iframe = screen.getByTitle("Видео к теме");
    expect(iframe).toHaveAttribute(
      "src",
      "https://www.youtube.com/embed/dQw4w9WgXcQ",
    );
    expect(iframe).toHaveAttribute("sandbox");
  });

  it("renders nothing for invalid URL", () => {
    const { container } = render(
      <VideoEmbed videoUrl="https://evil.example.com/video" />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});
