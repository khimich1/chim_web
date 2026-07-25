import { API_URL, ApiError, API_FETCH_TIMEOUT_MS, apiFetch } from "@/lib/api/client";

export type HandoffPurpose = "answer" | "feedback";

export interface HandoffCreateResponse {
  token: string;
  capture_url: string;
  expires_at: string;
}

export interface CaptureMetaResponse {
  purpose?: HandoffPurpose;
  session_id?: string | null;
  homework_id?: string | null;
  position?: number | null;
  task_title: string | null;
  question_preview: string | null;
  expires_at: string;
  already_has_photo: boolean;
  staged_image_id?: string | null;
  staged_image_url?: string | null;
}

export interface CaptureUploadResponse {
  purpose?: HandoffPurpose;
  position?: number | null;
  answer_image_ids?: string[];
  answer_image_urls?: string[];
  staged_image_id?: string | null;
  staged_image_url?: string | null;
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

export function createFeedbackHandoff(
  assignmentId: string,
  position?: number | null,
): Promise<HandoffCreateResponse> {
  return apiFetch<HandoffCreateResponse>(
    `/api/homework/${assignmentId}/feedback-handoff`,
    {
      method: "POST",
      body: JSON.stringify(
        position === undefined ? {} : { position },
      ),
    },
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
