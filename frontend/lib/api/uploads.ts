import { API_URL, ApiError, API_FETCH_TIMEOUT_MS } from "@/lib/api/client";
import type { UploadAudioResponse, UploadImageResponse } from "@/lib/api/types";

export async function uploadImage(file: File): Promise<UploadImageResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const useTimeout = process.env.VITEST !== "true";
  const response = await fetch(`${API_URL}/api/uploads/images`, {
    method: "POST",
    credentials: "include",
    body: formData,
    ...(useTimeout ? { signal: AbortSignal.timeout(API_FETCH_TIMEOUT_MS) } : {}),
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      if (typeof data?.detail === "string") {
        detail = data.detail;
      }
    } catch {
      // keep status text
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as UploadImageResponse;
}

export async function uploadAudio(
  file: File,
  durationSec: number,
): Promise<UploadAudioResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("duration_sec", String(durationSec));

  const useTimeout = process.env.VITEST !== "true";
  const response = await fetch(`${API_URL}/api/uploads/audio`, {
    method: "POST",
    credentials: "include",
    body: formData,
    ...(useTimeout ? { signal: AbortSignal.timeout(API_FETCH_TIMEOUT_MS) } : {}),
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      if (typeof data?.detail === "string") {
        detail = data.detail;
      }
    } catch {
      // keep status text
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as UploadAudioResponse;
}
