import type { TestStep } from "@/lib/api/types";

export function isCustomStep(step: TestStep): boolean {
  return (
    step.custom_task_id != null ||
    (step.question_blocks != null && step.question_blocks.length > 0)
  );
}

/** Teacher-authored self_check — excluded from session score (§1.9). */
export function isCustomSelfCheck(step: TestStep): boolean {
  return step.grading_mode === "self_check" && isCustomStep(step);
}

/** EGE content types 29–34 — included in session score (§1.10). */
export function isExamContentSelfCheck(step: TestStep): boolean {
  return step.grading_mode === "self_check" && !isCustomStep(step);
}

export function countsTowardScore(step: TestStep): boolean {
  return !isCustomSelfCheck(step);
}
