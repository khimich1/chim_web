import { API_URL, ApiError, apiFetch } from "@/lib/api/client";

export interface TutorPageContext {
  topic?: string | null;
  test_session_id?: string | null;
  homework_id?: string | null;
  step_position?: number | null;
  test_id?: number | null;
  solve_mode?: "explain_incorrect_step" | null;
}

export interface TutorSessionSummary {
  id: string;
  role_context: "student" | "teacher";
  page_context: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface TutorSourceCitation {
  source?: "lecture" | "lecture_qa" | "test" | null;
  topic?: string | null;
  chunk_idx?: number | null;
  chunk_title?: string | null;
}

export interface TutorMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: TutorSourceCitation[] | null;
  created_at: string;
}

export interface TutorSessionDetail extends TutorSessionSummary {
  messages: TutorMessage[];
}

export interface TutorMessageResponse {
  message_id: string;
  role: "assistant";
  content: string;
  sources: TutorSourceCitation[];
}

export interface TutorHealthResponse {
  rag_index_exists: boolean;
  openai_configured: boolean;
}

export function getTutorHealth(): Promise<TutorHealthResponse> {
  return apiFetch<TutorHealthResponse>("/api/tutor/health/tutor");
}

export function createTutorSession(
  pageContext?: TutorPageContext,
): Promise<TutorSessionSummary> {
  return apiFetch<TutorSessionSummary>("/api/tutor/sessions", {
    method: "POST",
    body: JSON.stringify({ page_context: pageContext ?? null }),
  });
}

export function listTutorSessions(): Promise<TutorSessionSummary[]> {
  return apiFetch<TutorSessionSummary[]>("/api/tutor/sessions");
}

export function getTutorSession(sessionId: string): Promise<TutorSessionDetail> {
  return apiFetch<TutorSessionDetail>(`/api/tutor/sessions/${sessionId}`);
}

export function sendTutorMessage(
  sessionId: string,
  content: string,
): Promise<TutorMessageResponse> {
  return apiFetch<TutorMessageResponse>(
    `/api/tutor/sessions/${sessionId}/messages`,
    {
      method: "POST",
      body: JSON.stringify({ content }),
    },
  );
}

export interface TutorStreamHandlers {
  onToken: (text: string) => void;
  onDone: (response: TutorMessageResponse) => void;
  onError?: (message: string) => void;
}

function parseSseBlock(block: string): { event: string; data: string } | null {
  const lines = block.split("\n").filter(Boolean);
  let event = "message";
  let data = "";
  for (const line of lines) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      data += line.slice(5).trim();
    }
  }
  if (!data) return null;
  return { event, data };
}

/** Stream assistant reply via SSE (Task 47 U1). */
export async function streamTutorMessage(
  sessionId: string,
  content: string,
  handlers: TutorStreamHandlers,
): Promise<void> {
  const response = await fetch(
    `${API_URL}/api/tutor/sessions/${sessionId}/messages/stream`,
    {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    },
  );

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      if (typeof payload?.detail === "string") {
        detail = payload.detail;
      }
    } catch {
      // non-JSON error body
    }
    throw new ApiError(response.status, detail);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Streaming not supported");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const parsed = parseSseBlock(block);
      if (parsed) {
        const payload = JSON.parse(parsed.data) as Record<string, unknown>;
        if (parsed.event === "token" && typeof payload.text === "string") {
          handlers.onToken(payload.text);
        } else if (parsed.event === "done") {
          handlers.onDone({
            message_id: String(payload.message_id),
            role: "assistant",
            content: String(payload.content ?? ""),
            sources: Array.isArray(payload.sources)
              ? (payload.sources as TutorMessageResponse["sources"])
              : [],
          });
        } else if (parsed.event === "error") {
          const message =
            typeof payload.detail === "string"
              ? payload.detail
              : "Ошибка стриминга";
          handlers.onError?.(message);
          throw new ApiError(503, message);
        }
      }
      boundary = buffer.indexOf("\n\n");
    }
  }
}

export function listStudentTutorSessions(
  studentId: string,
): Promise<TutorSessionSummary[]> {
  return apiFetch<TutorSessionSummary[]>(
    `/api/tutor/students/${studentId}/sessions`,
  );
}
