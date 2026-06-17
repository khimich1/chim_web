import Link from "next/link";

import { formatSessionTitle } from "@/components/tests/session-utils";
import { DecorativeBlobs } from "@/components/ui/DecorativeBlobs";
import type { TestSession } from "@/lib/api/types";

export function SessionSummary({ session }: { session: TestSession }) {
  const score = session.score ?? 0;
  const maxScore = session.max_score ?? session.total_steps;
  const percent =
    maxScore > 0 ? Math.round((score / maxScore) * 100) : 0;

  return (
    <div className="relative isolate min-w-0 overflow-hidden rounded-xl">
      <DecorativeBlobs scoped />

      <div className="relative z-10 flex flex-col gap-6">
        <article className="chem-card overflow-hidden rounded-xl">
          <header className="bg-chem-teal px-4 py-5 text-center text-white sm:px-5">
            <p className="text-xs font-medium uppercase tracking-wide text-white/75">
              Результат
            </p>
            <p className="mt-2 text-4xl font-bold tabular-nums">
              {score} / {maxScore}
            </p>
            <p className="mt-1 text-sm text-white/85">
              {formatSessionTitle(session)}
            </p>
            <span className="chem-progress-pill__percent mt-3 inline-block">
              {percent}%
            </span>
          </header>
        </article>

        <ul className="chem-card divide-y divide-zinc-200 overflow-hidden rounded-xl">
          {session.steps.map((step, index) => (
            <li
              key={step.position}
              className="flex items-center justify-between gap-3 px-4 py-3.5 text-sm sm:px-5"
            >
              <span className="flex min-w-0 items-center gap-3 text-zinc-800">
                <span
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-chem-teal-soft text-xs font-bold text-chem-teal-dark"
                  aria-hidden="true"
                >
                  {index + 1}
                </span>
                <span className="min-w-0 truncate">
                  Задание {step.type}
                  {step.hint_used ? (
                    <span className="ml-2 text-xs text-zinc-400">
                      (с подсказкой)
                    </span>
                  ) : null}
                </span>
              </span>
              <span
                className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${
                  step.is_correct === true
                    ? "chem-verdict-correct"
                    : step.is_correct === false
                      ? "chem-verdict-incorrect"
                      : "bg-zinc-100 text-zinc-500"
                }`}
              >
                {step.is_correct === true
                  ? "✓ Верно"
                  : step.is_correct === false
                    ? "✗ Неверно"
                    : "— Не отвечено"}
              </span>
            </li>
          ))}
        </ul>

        <div className="flex justify-center pb-2">
          <Link
            href="/student/tests"
            className="chem-btn-primary inline-flex min-h-[44px] items-center px-5 py-2.5 text-sm"
          >
            К списку тестов
          </Link>
        </div>
      </div>
    </div>
  );
}
