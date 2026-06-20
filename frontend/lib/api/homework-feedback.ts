import { API_URL, ApiError, API_FETCH_TIMEOUT_MS, apiFetch } from "@/lib/api/client";
import type {
  StepFeedbackContent,
  StepFeedbackInput,
  StepFeedbackRead,
  StudentHomeworkFeedback,
} from "@/lib/api/types";

export function saveStepFeedback(
  homeworkId: string,
  position: number,
  input: StepFeedbackInput,
): Promise<StepFeedbackRead> {
  return apiFetch<StepFeedbackRead>(
    `/api/homework/${homeworkId}/steps/${position}/feedback`,
    {
      method: "PUT",
      body: JSON.stringify(input),
    },
  );
}

export function saveSubmissionFeedback(
  homeworkId: string,
  input: StepFeedbackInput,
): Promise<StepFeedbackContent> {
  return apiFetch<StepFeedbackContent>(
    `/api/homework/${homeworkId}/submission-feedback`,
    {
      method: "PUT",
      body: JSON.stringify(input),
    },
  );
}

export function getStudentHomeworkFeedback(
  homeworkId: string,
): Promise<StudentHomeworkFeedback> {
  return apiFetch<StudentHomeworkFeedback>(
    `/api/student/homework/${homeworkId}/feedback`,
  );
}
