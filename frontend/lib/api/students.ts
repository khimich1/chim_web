import { apiFetch } from "@/lib/api/client";
import type { Student, Track } from "@/lib/api/types";

export interface CreateStudentInput {
  email: string;
  password: string;
  track: Track;
}

export function listStudents(): Promise<Student[]> {
  return apiFetch<Student[]>("/api/students");
}

export function createStudent(input: CreateStudentInput): Promise<Student> {
  return apiFetch<Student>("/api/students", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
