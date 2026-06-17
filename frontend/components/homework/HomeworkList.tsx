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

export function HomeworkList({
  assignments,
  detailBasePath,
}: {
  assignments: HomeworkAssignment[];
  detailBasePath: "/student/homework" | "/teacher/homework";
}) {
  if (assignments.length === 0) {
    return (
      <p className="text-sm text-zinc-500">Домашних заданий пока нет.</p>
    );
  }

  return (
    <ul className="chem-card divide-y divide-zinc-200 rounded-lg">
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
          <li key={assignment.id} className="px-4 py-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <Link
                  href={`${detailBasePath}/${assignment.id}`}
                  className="font-medium text-zinc-900 hover:text-chem-royal"
                >
                  {assignment.title}
                </Link>
                {assignment.student_email ? (
                  <p className="mt-1 text-sm text-zinc-600">
                    {assignment.student_email}
                  </p>
                ) : null}
                <p className="mt-1 text-sm text-zinc-500">
                  {homeworkItemsSummary(assignment.items)}
                </p>
                {progressLabel ? (
                  <p className="mt-1 text-sm text-zinc-500">{progressLabel}</p>
                ) : null}
                {assignment.submission?.score != null ? (
                  <p className="mt-1 text-sm text-chem-green">
                    Балл: {assignment.submission.score} /{" "}
                    {assignment.submission.max_score ?? "—"}
                  </p>
                ) : null}
              </div>
              <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-medium text-zinc-700">
                {STATUS_LABELS[assignment.status]}
              </span>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
