import { API_URL, ApiError, API_FETCH_TIMEOUT_MS, apiFetch } from "@/lib/api/client";

export interface HandoffCreateResponse {
  token: string;
  capture_url: string;
  expires_at: string;
}

export interface CaptureMetaResponse {
  session_id: string;
  position: number;
  task_title: string | null;
  question_preview: string | null;
  expires_at: string;
  already_has_photo: boolean;
}

export interface CaptureUploadResponse {
  position: number;
  answer_image_id: string;
  answer_image_url: string;
}

export function createHandoff(
  sessionId: string,
  position: number,
): Promise<HandoffCreateResponse> {
  return apiFetch<HandoffCreateResponse>(
    `/api/tests/sessions/${sessionId}/steps/${position}/handoff`,
    { method: "POST" },
  );
}

export function getCaptureMeta(token: string): Promise<CaptureMetaResponse> {
  return apiFetch<CaptureMetaResponse>(`/api/capture/${token}`);
}

export async function captureUpload(
  token: string,
  file: File,
): Promise<CaptureUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const useTimeout = process.env.VITEST !== "true";
  const response = await fetch(`${API_URL}/api/capture/${token}`, {
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

  return (await response.json()) as CaptureUploadResponse;
}
