import { apiFetch } from "@/lib/api/client";

export interface TutorPageContext {
  topic?: string | null;
  test_session_id?: string | null;
  homework_id?: string | null;
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

export function listStudentTutorSessions(
  studentId: string,
): Promise<TutorSessionSummary[]> {
  return apiFetch<TutorSessionSummary[]>(
    `/api/tutor/students/${studentId}/sessions`,
  );
}
