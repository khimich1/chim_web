import { apiFetch } from "@/lib/api/client";
import type { Student, Track } from "@/lib/api/types";

export interface CreateStudentInput {
  email: string;
  password: string;
  track: Track;
}

export interface StudentPasswordReset {
  temporary_password: string;
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

export function deleteStudent(id: string): Promise<void> {
  return apiFetch<void>(`/api/students/${id}`, {
    method: "DELETE",
  });
}

export function resetStudentPassword(id: string): Promise<StudentPasswordReset> {
  return apiFetch<StudentPasswordReset>(`/api/students/${id}/reset-password`, {
    method: "POST",
  });
}
