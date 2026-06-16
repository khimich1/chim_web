import "server-only";

import { cookies } from "next/headers";

import { API_URL } from "@/lib/api/client";
import type { User } from "@/lib/api/types";

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
