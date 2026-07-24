import { apiFetch } from "@/lib/api/client";
import type {
  CreateHomeworkTemplateInput,
  HomeworkAssignment,
  HomeworkTemplate,
  UpdateHomeworkTemplateInput,
} from "@/lib/api/types";

export type AssignHomeworkTemplateInput =
  | { student_id: string; due_at?: string | null }
  | { group_id: string; due_at?: string | null };

export function listHomeworkTemplates(): Promise<HomeworkTemplate[]> {
  return apiFetch<HomeworkTemplate[]>("/api/homework/templates");
}

export function getHomeworkTemplate(id: string): Promise<HomeworkTemplate> {
  return apiFetch<HomeworkTemplate>(`/api/homework/templates/${id}`);
}

export function createHomeworkTemplate(
  input: CreateHomeworkTemplateInput,
): Promise<HomeworkTemplate> {
  return apiFetch<HomeworkTemplate>("/api/homework/templates", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateHomeworkTemplate(
  id: string,
  input: UpdateHomeworkTemplateInput,
): Promise<HomeworkTemplate> {
  return apiFetch<HomeworkTemplate>(`/api/homework/templates/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function deleteHomeworkTemplate(id: string): Promise<void> {
  return apiFetch<void>(`/api/homework/templates/${id}`, {
    method: "DELETE",
  });
}

export function assignHomeworkTemplate(
  id: string,
  input: AssignHomeworkTemplateInput,
): Promise<HomeworkAssignment[]> {
  return apiFetch<HomeworkAssignment[]>(`/api/homework/templates/${id}/assign`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}
