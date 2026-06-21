import Link from "next/link";

import type { HomeworkAssignment } from "@/lib/api/types";
import { formatHomeworkSubmissionProgress } from "@/lib/homework/format-submission-progress";

import { HomeworkReopenButton } from "./HomeworkReopenButton";
import { HomeworkSubmitButton } from "./HomeworkSubmitButton";

export function HomeworkSessionSummarySection({
  homeworkId,
  sessionId,
  homework,
}: {
  homeworkId: string;
  sessionId: string;
  homework: HomeworkAssignment | null;
}) {
  const homeworkLink = `/student/homework/${homeworkId}`;

  if (!homework || homework.status !== "submitted") {
    return (
      <section className="chem-card mt-8 rounded-lg p-6">
        <h2 className="text-sm font-semibold text-zinc-900">Домашнее задание</h2>
        <p className="mt-2 text-sm text-zinc-600">
          Тест завершён — сдайте задание преподавателю.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-4">
          <HomeworkSubmitButton homeworkId={homeworkId} sessionId={sessionId} />
          <Link href={homeworkLink} className="chem-link text-sm">
            К заданию
          </Link>
        </div>
      </section>
    );
  }

  const progressLabel = formatHomeworkSubmissionProgress(homework.submission);

  return (
    <section className="chem-card mt-8 rounded-lg p-6">
      <h2 className="text-sm font-semibold text-zinc-900">Домашнее задание</h2>
      <p
        className="mt-2 text-sm font-medium text-[var(--text-positive)]"
        aria-live="polite"
      >
        Задание сдано{progressLabel}
        {homework.submission?.score != null
          ? ` — балл ${homework.submission.score} / ${homework.submission.max_score}`
          : ""}
        .
      </p>
      <div className="mt-4 flex flex-col gap-4">
        <Link href={homeworkLink} className="chem-link w-fit text-sm">
          К заданию
        </Link>
        {homework.can_reopen ? (
          <div>
            <p className="mb-2 text-sm text-zinc-600">
              Можно досдать оставшиеся задания и обновить результат.
            </p>
            <HomeworkReopenButton homeworkId={homeworkId} />
          </div>
        ) : null}
      </div>
    </section>
  );
}
