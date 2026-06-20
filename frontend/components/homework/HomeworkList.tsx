"use client";

import Link from "next/link";

import type { HomeworkAssignment } from "@/lib/api/types";

import { homeworkItemsSummary } from "./homework-utils";

const STATUS_LABELS: Record<HomeworkAssignment["status"], string> = {
  assigned: "Назначено",
  in_progress: "В работе",
  submitted: "Сдано",
  reviewed: "Проверено",
};

const STATUS_BADGE: Record<HomeworkAssignment["status"], string> = {
  assigned: "bg-chem-teal-soft text-chem-teal-dark",
  in_progress:
    "bg-[color-mix(in_srgb,var(--chem-gold)_28%,white)] text-[#5c4200]",
  submitted:
    "bg-[color-mix(in_srgb,var(--chem-green)_15%,white)] text-[var(--text-positive)]",
  reviewed:
    "bg-[color-mix(in_srgb,var(--chem-navy)_12%,white)] text-chem-navy",
};

export function HomeworkList({
  assignments,
  detailBasePath,
}: {
  assignments: HomeworkAssignment[];
  detailBasePath: "/student/homework" | "/teacher/homework";
}) {
  if (assignments.length === 0) {
    return (
      <p className="text-sm text-zinc-500" aria-live="polite">
        Домашних заданий пока нет.
      </p>
    );
  }

  return (
    <ul className="flex min-w-0 flex-col gap-4">
      {assignments.map((assignment) => {
        const completedCount = assignment.progress.filter(
          (row) => row.completed,
        ).length;
        const totalItems = assignment.items.length;
        const progressLabel =
          assignment.status === "submitted"
            ? null
            : totalItems > 0
              ? `${completedCount} / ${totalItems} пунктов`
              : null;

        return (
          <li key={assignment.id} className="chem-card min-w-0 overflow-hidden rounded-xl">
            <div className="flex flex-wrap items-center justify-between gap-2 bg-chem-teal px-4 py-3 sm:px-5">
              <h2 className="min-w-0 text-base font-semibold">
                <Link
                  href={`${detailBasePath}/${assignment.id}`}
                  className="text-white hover:underline focus-visible:underline"
                >
                  {assignment.title}
                </Link>
              </h2>
              <span
                className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_BADGE[assignment.status]}`}
              >
                {STATUS_LABELS[assignment.status]}
              </span>
              {assignment.has_teacher_feedback ? (
                <span className="shrink-0 rounded-full bg-chem-navy px-2.5 py-0.5 text-xs font-semibold text-white">
                  Есть разбор
                </span>
              ) : null}
            </div>

            <div className="space-y-1 px-4 py-4 sm:px-5">
              {assignment.student_email ? (
                <p className="text-sm text-zinc-600">{assignment.student_email}</p>
              ) : null}
              <p className="text-sm text-zinc-600">
                {homeworkItemsSummary(assignment.items)}
              </p>
              {progressLabel ? (
                <p className="text-sm text-zinc-500" aria-live="polite">
                  {progressLabel}
                </p>
              ) : null}
              {assignment.submission?.score != null ? (
                <p className="text-sm font-medium text-[var(--text-positive)]">
                  Балл: {assignment.submission.score} /{" "}
                  {assignment.submission.max_score ?? "—"}
                </p>
              ) : null}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
