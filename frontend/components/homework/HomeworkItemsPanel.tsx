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
      <p className="text-sm text-chem-green">
        Задание сдано
        {homework.submission?.score != null
          ? ` — балл ${homework.submission.score} / ${homework.submission.max_score}`
          : ""}
        .
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <ol className="flex flex-col gap-4">
        {homework.items.map((item, index) => {
          const completed = progressForIndex(homework, index);
          return (
            <li
              key={`${item.kind}-${index}`}
              className="rounded-lg border border-zinc-200 p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <p className="text-sm font-medium text-zinc-900">
                  {index + 1}. {formatHomeworkItemLabel(item)}
                </p>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    completed
                      ? "bg-chem-green/10 text-chem-green"
                      : "bg-zinc-100 text-zinc-600"
                  }`}
                >
                  {completed ? "Выполнено" : "Не выполнено"}
                </span>
              </div>

              {!completed && item.kind === "lecture" ? (
                <div className="mt-4 flex flex-col gap-3 border-t border-zinc-100 pt-4">
                  <p className="text-sm text-zinc-600">
                    Прочитайте лекцию по теме «{item.topic}», затем отметьте
                    пункт как прочитанный.
                  </p>
                  <Link
                    href={`/student/textbook/${encodeURIComponent(item.topic)}`}
                    className="chem-btn-primary inline-flex w-fit px-4 py-2 text-sm"
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
            </li>
          );
        })}
      </ol>

      {hasTestItems ? (
        <section className="rounded-lg border border-zinc-200 p-4">
          <h3 className="text-sm font-medium text-zinc-900">Тестовая часть</h3>
          <p className="mt-1 text-sm text-zinc-600">
            Все тестовые пункты проходятся в одной сессии — задания из разных
            вариантов идут подряд.
          </p>
          {!allLecturesDone ? (
            <p className="mt-3 text-sm text-amber-700">
              Сначала отметьте все лекции как прочитанные, затем начните тест.
            </p>
          ) : (
            <div className="mt-4 border-t border-zinc-100 pt-4">
              <TestHomeworkActions homeworkId={homework.id} />
            </div>
          )}
        </section>
      ) : null}

      {!hasTestItems && allLecturesDone ? (
        <section className="rounded-lg border border-dashed border-zinc-300 p-4">
          <h3 className="text-sm font-medium text-zinc-900">Сдача задания</h3>
          <p className="mt-1 text-sm text-zinc-600">
            Все лекции отмечены — можно сдать задание.
          </p>
          <div className="mt-4">
            <HomeworkSubmitButton homeworkId={homework.id} />
          </div>
        </section>
      ) : null}

      {hasTestItems && allLecturesDone ? (
        <section className="rounded-lg border border-dashed border-zinc-300 p-4">
          <h3 className="text-sm font-medium text-zinc-900">Сдача задания</h3>
          <p className="mt-1 text-sm text-zinc-600">
            Если тест уже завершён, сдайте задание здесь. Иначе начните тестовую
            часть выше.
          </p>
          <div className="mt-4">
            <HomeworkSubmitButton homeworkId={homework.id} />
          </div>
        </section>
      ) : null}
    </div>
  );
}
