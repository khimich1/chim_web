import { apiFetch } from "@/lib/api/client";
import type {
  CreateHomeworkInput,
  HomeworkAssignment,
  HomeworkItem,
} from "@/lib/api/types";

export function listHomework(): Promise<HomeworkAssignment[]> {
  return apiFetch<HomeworkAssignment[]>("/api/homework");
}

export function getHomework(id: string): Promise<HomeworkAssignment> {
  return apiFetch<HomeworkAssignment>(`/api/homework/${id}`);
}

export function createHomework(input: CreateHomeworkInput): Promise<HomeworkAssignment> {
  return apiFetch<HomeworkAssignment>("/api/homework", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function submitHomework(
  id: string,
  testSessionId?: string,
): Promise<HomeworkAssignment> {
  return apiFetch<HomeworkAssignment>(`/api/homework/${id}/submit`, {
    method: "POST",
    body: JSON.stringify(
      testSessionId ? { test_session_id: testSessionId } : {},
    ),
  });
}

export function reopenHomework(id: string): Promise<HomeworkAssignment> {
  return apiFetch<HomeworkAssignment>(`/api/homework/${id}/reopen`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function completeHomeworkItem(
  homeworkId: string,
  itemIndex: number,
): Promise<HomeworkAssignment> {
  return apiFetch<HomeworkAssignment>(
    `/api/homework/${homeworkId}/items/${itemIndex}/complete`,
    { method: "POST", body: JSON.stringify({}) },
  );
}

export type { HomeworkItem };
