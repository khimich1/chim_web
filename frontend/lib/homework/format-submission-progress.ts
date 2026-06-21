export interface HomeworkProgressFields {
  answered_steps?: number | null;
  total_steps?: number | null;
  completion_percent?: number | null;
}

/** Suffix like ` (1/2, 50%)` when progress fields are present. */
export function formatHomeworkSubmissionProgress(
  submission: HomeworkProgressFields | null | undefined,
): string {
  if (
    submission?.answered_steps != null &&
    submission?.total_steps != null
  ) {
    const completion = submission.completion_percent ?? 0;
    return ` (${submission.answered_steps}/${submission.total_steps}, ${completion}%)`;
  }
  return "";
}
