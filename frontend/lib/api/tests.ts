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
  types?: number[],
): Promise<TestSession> {
  return apiFetch<TestSession>("/api/tests/sessions", {
    method: "POST",
    body: JSON.stringify({ variant_ref: variantRef, types: types ?? null }),
  });
}

export function getSession(sessionId: string): Promise<TestSession> {
  return apiFetch<TestSession>(`/api/tests/sessions/${sessionId}`);
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
