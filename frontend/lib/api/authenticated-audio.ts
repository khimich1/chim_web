import { API_FETCH_TIMEOUT_MS, API_URL } from "@/lib/api/client";
import { resolveImagePath } from "@/lib/api/authenticated-image";

/** Fetch authenticated upload audio as blob (httpOnly cookie auth). */
export async function fetchAuthenticatedAudioBlob(pathOrUrl: string): Promise<Blob> {
  const path = resolveImagePath(pathOrUrl);
  const useTimeout = process.env.VITEST !== "true";

  const response = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    ...(useTimeout ? { signal: AbortSignal.timeout(API_FETCH_TIMEOUT_MS) } : {}),
  });

  if (!response.ok) {
    throw new Error("Failed to load audio");
  }

  return response.blob();
}
