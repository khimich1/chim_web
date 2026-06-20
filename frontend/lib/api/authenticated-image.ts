import { API_FETCH_TIMEOUT_MS, API_URL } from "@/lib/api/client";

/** Normalize API path from relative or absolute upload URL. */
export function resolveImagePath(url: string): string {
  if (url.startsWith("http")) {
    return new URL(url).pathname;
  }
  return url;
}

/** Fetch an authenticated upload image as blob (httpOnly cookie auth). */
export async function fetchAuthenticatedImageBlob(pathOrUrl: string): Promise<Blob> {
  const path = resolveImagePath(pathOrUrl);
  const useTimeout = process.env.VITEST !== "true";

  const response = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    ...(useTimeout ? { signal: AbortSignal.timeout(API_FETCH_TIMEOUT_MS) } : {}),
  });

  if (!response.ok) {
    throw new Error("Failed to load image");
  }

  return response.blob();
}
