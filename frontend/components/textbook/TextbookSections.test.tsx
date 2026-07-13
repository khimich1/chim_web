import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { SectionPills } from "@/components/textbook/SectionPills";
import { TopicList } from "@/components/textbook/TopicList";

const sections = [
  { section_id: "basics", title: "Начала химии", topic_count: 1 },
  { section_id: "elements", title: "Химия элементов", topic_count: 0 },
  { section_id: "organic", title: "Органическая химия", topic_count: 1 },
];

const topics = [
  {
    topic: "Соли",
    chunk_count: 2,
    section: "basics",
    video_url: null,
  },
];

describe("SectionPills", () => {
  it("marks active section and links to shareable URLs", () => {
    render(<SectionPills sections={sections} activeSection="basics" />);

    const active = screen.getByRole("link", { name: /Начала химии/i });
    expect(active).toHaveAttribute("href", "/student/textbook?section=basics");
    expect(active).toHaveAttribute("aria-current", "page");

    expect(screen.getByRole("link", { name: /Органическая химия/i })).toHaveAttribute(
      "href",
      "/student/textbook?section=organic",
    );
  });
});

describe("TopicList", () => {
  it("preserves section in topic links", () => {
    render(<TopicList topics={topics} section="basics" />);

    expect(screen.getByRole("link", { name: /Соли/i })).toHaveAttribute(
      "href",
      "/student/textbook/%D0%A1%D0%BE%D0%BB%D0%B8?section=basics",
    );
  });

  it("shows empty state when section has no topics", () => {
    render(<TopicList topics={[]} section="elements" />);

    expect(screen.getByText("В этом разделе пока нет тем.")).toBeInTheDocument();
  });
});
