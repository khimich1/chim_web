import "server-only";

import { cookies } from "next/headers";

import { API_URL } from "@/lib/api/client";
import type {
  ChunkSummary,
  Student,
  TestSession,
  TestVariant,
  TextbookTopic,
  User,
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

export async function getTestVariants(): Promise<TestVariant[]> {
  return (await fetchWithCookies<TestVariant[]>("/api/tests/variants")) ?? [];
}

export async function getTestSession(
  sessionId: string,
): Promise<TestSession | null> {
  return fetchWithCookies<TestSession>(`/api/tests/sessions/${sessionId}`);
}
