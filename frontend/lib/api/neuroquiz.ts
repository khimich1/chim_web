import { apiFetch } from "@/lib/api/client";
import type {
  NeuroQuizSession,
  NeuroQuizSubmitResult,
} from "@/lib/api/types";

export function warmupNeuroQuiz(topic: string, chunkIdx: number): Promise<void> {
  return apiFetch<void>(
    `/api/neuroquiz/topics/${encodeURIComponent(topic)}/chunks/${chunkIdx}/warmup`,
    { method: "POST" },
  );
}

export function getNeuroQuizSession(
  topic: string,
  chunkIdx: number,
): Promise<NeuroQuizSession> {
  return apiFetch<NeuroQuizSession>(
    `/api/neuroquiz/topics/${encodeURIComponent(topic)}/chunks/${chunkIdx}`,
  );
}

export function answerNeuroQuiz(
  topic: string,
  chunkIdx: number,
  questionId: string,
  optionId: string,
): Promise<NeuroQuizSubmitResult> {
  return apiFetch<NeuroQuizSubmitResult>(
    `/api/neuroquiz/topics/${encodeURIComponent(topic)}/chunks/${chunkIdx}/answer`,
    {
      method: "POST",
      body: JSON.stringify({ question_id: questionId, option_id: optionId }),
    },
  );
}

export function skipNeuroQuiz(topic: string, chunkIdx: number): Promise<void> {
  return apiFetch<void>(
    `/api/neuroquiz/topics/${encodeURIComponent(topic)}/chunks/${chunkIdx}/skip`,
    { method: "POST" },
  );
}

export function voteNeuroQuiz(
  questionId: string,
  value: "like" | "dislike",
): Promise<void> {
  return apiFetch<void>(`/api/neuroquiz/questions/${questionId}/vote`, {
    method: "POST",
    body: JSON.stringify({ value }),
  });
}
