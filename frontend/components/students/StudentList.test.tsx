import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { StudentList } from "@/components/students/StudentList";
import type { Student, TeacherStudentStats } from "@/lib/api/types";

const students: Student[] = [
  {
    id: "11111111-1111-1111-1111-111111111111",
    email: "student-a@example.com",
    track: "ege",
    created_at: "2026-06-01T10:00:00Z",
  },
];

const stats: TeacherStudentStats[] = [
  {
    id: "11111111-1111-1111-1111-111111111111",
    email: "student-a@example.com",
    display_name: "Аня",
    total_points: 120,
    week_points: 40,
    streak: 2,
    tasks_solved: 8,
    total_minutes: 45,
    last_active_date: "2026-06-18",
  },
];

describe("StudentList", () => {
  it("renders gamification columns when stats are provided", () => {
    render(<StudentList students={students} stats={stats} />);

    expect(screen.getByText("Аня")).toBeInTheDocument();
    expect(screen.getByText("student-a@example.com")).toBeInTheDocument();
    expect(screen.getByText("40")).toBeInTheDocument();
    expect(screen.getByText("/ 120")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
    expect(screen.getByText("45 мин")).toBeInTheDocument();
    expect(screen.getByText("Баллы (нед.)")).toBeInTheDocument();
  });

  it("falls back to created date when stats are omitted", () => {
    render(<StudentList students={students} />);

    expect(screen.getByText("Создан")).toBeInTheDocument();
    expect(screen.queryByText("Баллы (нед.)")).not.toBeInTheDocument();
  });

  it("shows empty state when there are no students", () => {
    render(<StudentList students={[]} stats={[]} />);

    expect(
      screen.getByText("Пока нет учеников. Создайте первого."),
    ).toBeInTheDocument();
  });
});
