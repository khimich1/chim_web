import { apiFetch } from "@/lib/api/client";
import type { Track } from "@/lib/api/types";

export interface StudentGroupMember {
  id: string;
  email: string;
  track: Track | null;
}

export interface StudentGroupSummary {
  id: string;
  teacher_id: string;
  name: string;
  member_count: number;
  created_at: string;
}

export interface StudentGroupDetail extends StudentGroupSummary {
  members: StudentGroupMember[];
}

export function listTeacherGroups(): Promise<StudentGroupSummary[]> {
  return apiFetch<StudentGroupSummary[]>("/api/teacher/groups");
}

export function getTeacherGroup(id: string): Promise<StudentGroupDetail> {
  return apiFetch<StudentGroupDetail>(`/api/teacher/groups/${id}`);
}

export function createTeacherGroup(input?: {
  name?: string | null;
}): Promise<StudentGroupDetail> {
  return apiFetch<StudentGroupDetail>("/api/teacher/groups", {
    method: "POST",
    body: JSON.stringify(input ?? {}),
  });
}

export function renameTeacherGroup(
  id: string,
  name: string,
): Promise<StudentGroupDetail> {
  return apiFetch<StudentGroupDetail>(`/api/teacher/groups/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
}

export function deleteTeacherGroup(id: string): Promise<void> {
  return apiFetch<void>(`/api/teacher/groups/${id}`, {
    method: "DELETE",
  });
}

export function replaceTeacherGroupMembers(
  id: string,
  studentIds: string[],
): Promise<StudentGroupDetail> {
  return apiFetch<StudentGroupDetail>(`/api/teacher/groups/${id}/members`, {
    method: "PUT",
    body: JSON.stringify({ student_ids: studentIds }),
  });
}
