import { formatHomeworkSubmissionProgress } from "@/lib/homework/format-submission-progress";
import type { Notification } from "@/lib/api/types";

export function formatHomeworkSubmittedNotification(
  payload: Notification["payload"],
): string {
  const base = `${payload.student_email} сдал(а) «${payload.homework_title}»`;
  const progress = formatHomeworkSubmissionProgress(payload);
  return progress ? `${base}${progress}` : base;
}
