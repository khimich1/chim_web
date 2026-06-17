"use client";

import Link from "next/link";

import type { HomeworkAssignment } from "@/lib/api/types";

import { formatHomeworkItemLabel, isTestHomeworkItem } from "./homework-utils";
import { HomeworkSubmitButton } from "./HomeworkSubmitButton";
import { LectureHomeworkSubmit } from "./LectureHomework";
import { TestHomeworkActions } from "./TestHomeworkActions";

function progressForIndex(
  homework: HomeworkAssignment,
  itemIndex: number,
): boolean {
  return (
    homework.progress.find((row) => row.item_index === itemIndex)?.completed ??
    false
  );
}

export function HomeworkItemsPanel({
  homework,
}: {
  homework: HomeworkAssignment;
}) {
  const isSubmitted = homework.status === "submitted";
  const hasTestItems = homework.items.some((item) => isTestHomeworkItem(item));
  const allLecturesDone = homework.items.every(
    (item, index) =>
      item.kind !== "lecture" || progressForIndex(homework, index),
  );

  if (isSubmitted) {
    return (
      <p
        className="text-sm font-medium text-[var(--text-positive)]"
        aria-live="polite"
      >
        Задание сдано
        {homework.submission?.score != null
          ? ` — балл ${homework.submission.score} / ${homework.submission.max_score}`
          : ""}
        .
      </p>
    );
  }

  return (
    <div className="flex min-w-0 flex-col gap-6">
      <ol className="flex flex-col gap-4">
        {homework.items.map((item, index) => {
          const completed = progressForIndex(homework, index);
          return (
            <li
              key={`${item.kind}-${index}`}
              className="chem-card min-w-0 overflow-hidden rounded-xl"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 bg-chem-teal-soft px-4 py-3 sm:px-5">
                <h3 className="min-w-0 text-sm font-semibold text-chem-teal-dark">
                  {index + 1}. {formatHomeworkItemLabel(item)}
                </h3>
                <span
                  className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                    completed
                      ? "bg-[color-mix(in_srgb,var(--chem-green)_15%,white)] text-[var(--text-positive)]"
                      : "bg-white text-zinc-600"
                  }`}
                  aria-live="polite"
                >
                  {completed ? "Выполнено" : "Не выполнено"}
                </span>
              </div>

              <div className="px-4 py-4 sm:px-5">
                {!completed && item.kind === "lecture" ? (
                  <div className="flex flex-col gap-3 border-t border-zinc-100 pt-4">
                    <p className="text-sm text-zinc-600">
                      Прочитайте лекцию по теме «{item.topic}», затем отметьте
                      пункт как прочитанный.
                    </p>
                    <Link
                      href={`/student/textbook/${encodeURIComponent(item.topic)}`}
                      className="chem-btn-primary inline-flex min-h-[44px] w-fit items-center px-4 py-2 text-sm"
                    >
                      Открыть тему «{item.topic}»
                    </Link>
                    <LectureHomeworkSubmit
                      homeworkId={homework.id}
                      itemIndex={index}
                      topic={item.topic}
                    />
                  </div>
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>

      {hasTestItems ? (
        <section
          className="chem-card min-w-0 overflow-hidden rounded-xl"
          aria-labelledby="homework-test-section"
        >
          <h3
            id="homework-test-section"
            className="bg-chem-teal px-4 py-3 text-sm font-semibold text-white sm:px-5"
          >
            Тестовая часть
          </h3>
          <div className="px-4 py-4 sm:px-5">
            <p className="text-sm text-zinc-600">
              Все тестовые пункты проходятся в одной сессии — задания из разных
              вариантов идут подряд.
            </p>
            {!allLecturesDone ? (
              <p className="mt-3 text-sm text-amber-800" aria-live="polite">
                Сначала отметьте все лекции как прочитанные, затем начните тест.
              </p>
            ) : (
              <div className="mt-4 border-t border-zinc-100 pt-4">
                <TestHomeworkActions homeworkId={homework.id} />
              </div>
            )}
          </div>
        </section>
      ) : null}

      {!hasTestItems && allLecturesDone ? (
        <section
          className="chem-card min-w-0 overflow-hidden rounded-xl border-dashed"
          aria-labelledby="homework-submit-section"
        >
          <h3
            id="homework-submit-section"
            className="bg-chem-teal-soft px-4 py-3 text-sm font-semibold text-chem-teal-dark sm:px-5"
          >
            Сдача задания
          </h3>
          <div className="px-4 py-4 sm:px-5">
            <p className="text-sm text-zinc-600">
              Все лекции отмечены — можно сдать задание.
            </p>
            <div className="mt-4">
              <HomeworkSubmitButton homeworkId={homework.id} />
            </div>
          </div>
        </section>
      ) : null}

      {hasTestItems && allLecturesDone ? (
        <section
          className="chem-card min-w-0 overflow-hidden rounded-xl border-dashed"
          aria-labelledby="homework-submit-after-test"
        >
          <h3
            id="homework-submit-after-test"
            className="bg-chem-teal-soft px-4 py-3 text-sm font-semibold text-chem-teal-dark sm:px-5"
          >
            Сдача задания
          </h3>
          <div className="px-4 py-4 sm:px-5">
            <p className="text-sm text-zinc-600">
              Если тест уже завершён, сдайте задание здесь. Иначе начните тестовую
              часть выше.
            </p>
            <div className="mt-4">
              <HomeworkSubmitButton homeworkId={homework.id} />
            </div>
          </div>
        </section>
      ) : null}
    </div>
  );
}
