import "server-only";

import { cookies } from "next/headers";

import { API_URL } from "@/lib/api/client";
import type {
  ChunkSummary,
  CustomTask,
  CustomThemeListItem,
  HomeworkAssignment,
  Notification,
  Student,
  TeacherStudentStats,
  TeacherTheme,
  TestSession,
  TestTaskType,
  TestVariant,
  TextbookTopic,
  Track,
  User,
  OnboardingStatus,
  OnboardingWelcome,
} from "@/lib/api/types";
/**
 * Server-side current-user lookup for protected layouts. Forwards the incoming
 * request cookies to FastAPI; returns null when the session is missing/invalid.
 */
export async function getCurrentUser(): Promise<User | null> {
  const cookieHeader = (await cookies()).toString();
  if (!cookieHeader) {
    return null;
  }

  const response = await fetch(`${API_URL}/api/auth/me`, {
    headers: { cookie: cookieHeader },
    cache: "no-store",
  });

  if (!response.ok) {
    return null;
  }
  return (await response.json()) as User;
}

/**
 * Server-side students list for teacher pages. Forwards cookies to FastAPI.
 */
export async function getStudents(): Promise<Student[]> {
  const cookieHeader = (await cookies()).toString();
  if (!cookieHeader) {
    return [];
  }

  const response = await fetch(`${API_URL}/api/students`, {
    headers: { cookie: cookieHeader },
    cache: "no-store",
  });

  if (!response.ok) {
    return [];
  }
  return (await response.json()) as Student[];
}

/** Server-side student stats for teacher pages (Task 62). */
export async function getTeacherStudentsStats(): Promise<TeacherStudentStats[]> {
  return (
    (await fetchWithCookies<TeacherStudentStats[]>(
      "/api/teacher/students/stats",
    )) ?? []
  );
}

async function fetchWithCookies<T>(path: string): Promise<T | null> {
  const cookieHeader = (await cookies()).toString();
  if (!cookieHeader) {
    return null;
  }

  const response = await fetch(`${API_URL}${path}`, {
    headers: { cookie: cookieHeader },
    cache: "no-store",
  });

  if (!response.ok) {
    return null;
  }
  return (await response.json()) as T;
}

export async function getTextbookTopics(): Promise<TextbookTopic[]> {
  return (await fetchWithCookies<TextbookTopic[]>("/api/textbook/topics")) ?? [];
}

export async function getTextbookChunks(topic: string): Promise<ChunkSummary[]> {
  return (
    (await fetchWithCookies<ChunkSummary[]>(
      `/api/textbook/topics/${encodeURIComponent(topic)}/chunks`,
    )) ?? []
  );
}

export async function getTestTaskTypes(track?: Track): Promise<TestTaskType[]> {
  const query = track ? `?track=${track}` : "";
  return (
    (await fetchWithCookies<TestTaskType[]>(`/api/tests/task-types${query}`)) ??
    []
  );
}

export async function getTestVariants(track?: Track): Promise<TestVariant[]> {
  const query = track ? `?track=${track}` : "";
  return (await fetchWithCookies<TestVariant[]>(`/api/tests/variants${query}`)) ?? [];
}

export async function getTestSession(
  sessionId: string,
): Promise<TestSession | null> {
  return fetchWithCookies<TestSession>(`/api/tests/sessions/${sessionId}`);
}

export async function getHomeworkList(): Promise<HomeworkAssignment[]> {
  return (await fetchWithCookies<HomeworkAssignment[]>("/api/homework")) ?? [];
}

export async function getOnboardingStatus(): Promise<OnboardingStatus | null> {
  return fetchWithCookies<OnboardingStatus>("/api/students/me/onboarding");
}

export async function getOnboardingWelcome(): Promise<OnboardingWelcome | null> {
  return fetchWithCookies<OnboardingWelcome>("/api/students/me/onboarding/welcome");
}

export async function getHomework(
  id: string,
): Promise<HomeworkAssignment | null> {
  return fetchWithCookies<HomeworkAssignment>(`/api/homework/${id}`);
}

export async function getNotifications(): Promise<Notification[]> {
  return (await fetchWithCookies<Notification[]>("/api/notifications")) ?? [];
}

export async function getNotificationUnreadCount(): Promise<number> {
  const result = await fetchWithCookies<{ count: number }>(
    "/api/notifications/unread-count",
  );
  return result?.count ?? 0;
}

export interface TutorSessionSummaryServer {
  id: string;
  role_context: "student" | "teacher";
  page_context: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface TutorSessionDetailServer extends TutorSessionSummaryServer {
  messages: Array<{
    id: string;
    role: "user" | "assistant";
    content: string;
    sources?: Array<Record<string, unknown>> | null;
    created_at: string;
  }>;
}

export async function listStudentTutorSessions(
  studentId: string,
): Promise<TutorSessionSummaryServer[]> {
  return (
    (await fetchWithCookies<TutorSessionSummaryServer[]>(
      `/api/tutor/students/${studentId}/sessions`,
    )) ?? []
  );
}

export async function getTutorSessionDetail(
  sessionId: string,
): Promise<TutorSessionDetailServer | null> {
  return fetchWithCookies<TutorSessionDetailServer>(
    `/api/tutor/sessions/${sessionId}`,
  );
}

export async function getTeacherThemes(): Promise<TeacherTheme[]> {
  return (await fetchWithCookies<TeacherTheme[]>("/api/teacher/themes")) ?? [];
}

export async function getTeacherTheme(id: string): Promise<TeacherTheme | null> {
  return fetchWithCookies<TeacherTheme>(`/api/teacher/themes/${id}`);
}

export async function getTeacherThemeTasks(
  themeId: string,
): Promise<CustomTask[]> {
  return (
    (await fetchWithCookies<CustomTask[]>(
      `/api/teacher/themes/${themeId}/tasks`,
    )) ?? []
  );
}

/** @deprecated Use getTeacherThemes — API includes task_count (Task 94). */
export async function getTeacherThemesWithTaskCounts(): Promise<TeacherTheme[]> {
  return getTeacherThemes();
}

export async function getCustomThemes(): Promise<CustomThemeListItem[]> {
  return (
    (await fetchWithCookies<CustomThemeListItem[]>("/api/custom-themes")) ?? []
  );
}
