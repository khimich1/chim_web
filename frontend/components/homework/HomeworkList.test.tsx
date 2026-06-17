import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { HomeworkList } from "@/components/homework/HomeworkList";
import type { HomeworkAssignment } from "@/lib/api/types";

const assignment: HomeworkAssignment = {
  id: "hw-1",
  student_id: "s1",
  student_email: "student@example.com",
  title: "Алканы и алкены",
  description: null,
  due_at: null,
  items: [
    { kind: "lecture", topic: "Алканы" },
    { kind: "test_variant", variant: "001.txt" },
  ],
  status: "in_progress",
  created_at: "2026-06-17T10:00:00Z",
  submission: null,
  progress: [{ item_index: 0, completed: true }],
};

describe("HomeworkList", () => {
  it("renders empty state", () => {
    render(<HomeworkList assignments={[]} detailBasePath="/student/homework" />);

    expect(screen.getByText("Домашних заданий пока нет.")).toBeInTheDocument();
  });

  it("renders assignment card with status and progress", () => {
    render(
      <HomeworkList assignments={[assignment]} detailBasePath="/student/homework" />,
    );

    expect(screen.getByRole("heading", { name: "Алканы и алкены" })).toBeInTheDocument();
    expect(screen.getByText("В работе")).toBeInTheDocument();
    expect(screen.getByText("1 / 2 пунктов")).toBeInTheDocument();
    expect(screen.getByText("student@example.com")).toBeInTheDocument();
  });

  it("links to homework detail", () => {
    render(
      <HomeworkList assignments={[assignment]} detailBasePath="/student/homework" />,
    );

    expect(screen.getByRole("link", { name: "Алканы и алкены" })).toHaveAttribute(
      "href",
      "/student/homework/hw-1",
    );
  });

  it("shows score when submitted", () => {
    const submitted: HomeworkAssignment = {
      ...assignment,
      status: "submitted",
      submission: {
        id: "sub-1",
        homework_id: "hw-1",
        score: 8,
        max_score: 10,
        submitted_at: "2026-06-17T12:00:00Z",
      },
    };

    render(
      <HomeworkList assignments={[submitted]} detailBasePath="/student/homework" />,
    );

    expect(screen.getByText("Сдано")).toBeInTheDocument();
    expect(screen.getByText(/Балл: 8 \/ 10/)).toBeInTheDocument();
  });
});
