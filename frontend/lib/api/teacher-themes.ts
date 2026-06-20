import { apiFetch } from "@/lib/api/client";
import type {
  CustomTask,
  CustomTaskCreateInput,
  CustomTaskUpdateInput,
  TeacherTheme,
  TeacherThemeCreateInput,
  TeacherThemeUpdateInput,
} from "@/lib/api/types";

export function listTeacherThemes(): Promise<TeacherTheme[]> {
  return apiFetch<TeacherTheme[]>("/api/teacher/themes");
}

export function createTeacherTheme(
  input: TeacherThemeCreateInput,
): Promise<TeacherTheme> {
  return apiFetch<TeacherTheme>("/api/teacher/themes", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getTeacherTheme(id: string): Promise<TeacherTheme> {
  return apiFetch<TeacherTheme>(`/api/teacher/themes/${id}`);
}

export function updateTeacherTheme(
  id: string,
  input: TeacherThemeUpdateInput,
): Promise<TeacherTheme> {
  return apiFetch<TeacherTheme>(`/api/teacher/themes/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function deleteTeacherTheme(id: string): Promise<void> {
  return apiFetch<void>(`/api/teacher/themes/${id}`, { method: "DELETE" });
}

export function listThemeTasks(themeId: string): Promise<CustomTask[]> {
  return apiFetch<CustomTask[]>(`/api/teacher/themes/${themeId}/tasks`);
}

export function createThemeTask(
  themeId: string,
  input: CustomTaskCreateInput,
): Promise<CustomTask> {
  return apiFetch<CustomTask>(`/api/teacher/themes/${themeId}/tasks`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateThemeTask(
  taskId: string,
  input: CustomTaskUpdateInput,
): Promise<CustomTask> {
  return apiFetch<CustomTask>(`/api/teacher/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function deleteThemeTask(taskId: string): Promise<void> {
  return apiFetch<void>(`/api/teacher/tasks/${taskId}`, { method: "DELETE" });
}
