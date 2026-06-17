import { apiFetch } from "@/lib/api/client";
import type {
  HintResult,
  StepCheckResult,
  TestSession,
  TestVariant,
} from "@/lib/api/types";

export function listVariants(): Promise<TestVariant[]> {
  return apiFetch<TestVariant[]>("/api/tests/variants");
}

export function createSession(
  variantRef: string,
  options?: { types?: number[]; homeworkAssignmentId?: string },
): Promise<TestSession> {
  return apiFetch<TestSession>("/api/tests/sessions", {
    method: "POST",
    body: JSON.stringify({
      variant_ref: variantRef,
      types: options?.types ?? null,
      homework_assignment_id: options?.homeworkAssignmentId ?? null,
    }),
  });
}

/** Aggregated test session for a multi-item homework assignment (SPEC §1.7). */
export function createHomeworkTestSession(
  homeworkAssignmentId: string,
): Promise<TestSession> {
  return apiFetch<TestSession>("/api/tests/sessions", {
    method: "POST",
    body: JSON.stringify({ homework_assignment_id: homeworkAssignmentId }),
  });
}

export function getSession(sessionId: string): Promise<TestSession> {
  return apiFetch<TestSession>(`/api/tests/sessions/${sessionId}`);
}

export function getActiveSession(
  params:
    | { variantRef: string; homeworkAssignmentId?: undefined }
    | { homeworkAssignmentId: string; variantRef?: undefined },
): Promise<ActiveSessionResult> {
  const search = new URLSearchParams();
  if ("variantRef" in params && params.variantRef) {
    search.set("variant_ref", params.variantRef);
  }
  if ("homeworkAssignmentId" in params && params.homeworkAssignmentId) {
    search.set("homework_assignment_id", params.homeworkAssignmentId);
  }
  return apiFetch<ActiveSessionResult>(
    `/api/tests/sessions/active?${search.toString()}`,
  );
}

export function checkStep(
  sessionId: string,
  position: number,
  answer: string,
): Promise<StepCheckResult> {
  return apiFetch<StepCheckResult>(
    `/api/tests/sessions/${sessionId}/steps/${position}/check`,
    {
      method: "POST",
      body: JSON.stringify({ answer }),
    },
  );
}

export function getHint(
  sessionId: string,
  position: number,
): Promise<HintResult> {
  return apiFetch<HintResult>(
    `/api/tests/sessions/${sessionId}/steps/${position}/hint`,
  );
}

export function completeSession(sessionId: string): Promise<unknown> {
  return apiFetch(`/api/tests/sessions/${sessionId}/complete`, {
    method: "POST",
  });
}
