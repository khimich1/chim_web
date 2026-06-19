import { apiFetch } from "@/lib/api/client";
import type {
  ActiveSessionResult,
  StepCheckResult,
  TestSession,
  TestTaskType,
  TestVariant,
} from "@/lib/api/types";

export function listVariants(): Promise<TestVariant[]> {
  return apiFetch<TestVariant[]>("/api/tests/variants");
}

export function listTaskTypes(): Promise<TestTaskType[]> {
  return apiFetch<TestTaskType[]>("/api/tests/task-types");
}

export function createSession(
  variantRefOrOptions:
    | string
    | { types: number[]; homeworkAssignmentId?: string },
  options?: { types?: number[]; homeworkAssignmentId?: string },
): Promise<TestSession> {
  const payload =
    typeof variantRefOrOptions === "string"
      ? {
          variant_ref: variantRefOrOptions,
          types: options?.types ?? null,
          homework_assignment_id: options?.homeworkAssignmentId ?? null,
        }
      : {
          variant_ref: null,
          types: variantRefOrOptions.types,
          homework_assignment_id:
            variantRefOrOptions.homeworkAssignmentId ?? null,
        };

  return apiFetch<TestSession>("/api/tests/sessions", {
    method: "POST",
    body: JSON.stringify(payload),
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
    | { variantRef: string; homeworkAssignmentId?: undefined; taskType?: undefined }
    | { homeworkAssignmentId: string; variantRef?: undefined; taskType?: undefined }
    | { taskType: number; variantRef?: undefined; homeworkAssignmentId?: undefined },
): Promise<ActiveSessionResult> {
  const search = new URLSearchParams();
  if ("variantRef" in params && params.variantRef) {
    search.set("variant_ref", params.variantRef);
  }
  if ("homeworkAssignmentId" in params && params.homeworkAssignmentId) {
    search.set("homework_assignment_id", params.homeworkAssignmentId);
  }
  if ("taskType" in params && params.taskType !== undefined) {
    search.set("task_type", String(params.taskType));
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

export function completeSession(sessionId: string): Promise<unknown> {
  return apiFetch(`/api/tests/sessions/${sessionId}/complete`, {
    method: "POST",
  });
}
