import { apiFetch } from "@/lib/api/client";
import type {
  ActiveSessionResult,
  StepCheckResult,
  StepCompareResult,
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
    | { types: number[]; homeworkAssignmentId?: string }
    | { customThemeId: string; taskIds?: string[] },
  options?: { types?: number[]; homeworkAssignmentId?: string },
): Promise<TestSession> {
  let payload: Record<string, unknown>;

  if (typeof variantRefOrOptions === "string") {
    payload = {
      variant_ref: variantRefOrOptions,
      types: options?.types ?? null,
      homework_assignment_id: options?.homeworkAssignmentId ?? null,
    };
  } else if ("customThemeId" in variantRefOrOptions) {
    payload = {
      custom_theme_id: variantRefOrOptions.customThemeId,
      task_ids: variantRefOrOptions.taskIds ?? null,
    };
  } else {
    payload = {
      variant_ref: null,
      types: variantRefOrOptions.types,
      homework_assignment_id:
        variantRefOrOptions.homeworkAssignmentId ?? null,
    };
  }

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
    | { variantRef: string; homeworkAssignmentId?: undefined; taskType?: undefined; customThemeId?: undefined }
    | { homeworkAssignmentId: string; variantRef?: undefined; taskType?: undefined; customThemeId?: undefined }
    | { taskType: number; variantRef?: undefined; homeworkAssignmentId?: undefined; customThemeId?: undefined }
    | { customThemeId: string; variantRef?: undefined; homeworkAssignmentId?: undefined; taskType?: undefined },
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
  if ("customThemeId" in params && params.customThemeId) {
    search.set("custom_theme_id", params.customThemeId);
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

export function compareStep(
  sessionId: string,
  position: number,
  answer: string,
): Promise<StepCompareResult> {
  return apiFetch<StepCompareResult>(
    `/api/tests/sessions/${sessionId}/steps/${position}/compare`,
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
