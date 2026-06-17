import Link from "next/link";

import { formatSessionTitle } from "@/components/tests/session-utils";
import type { TestSession } from "@/lib/api/types";

export function SessionSummary({ session }: { session: TestSession }) {
  const score = session.score ?? 0;
  const maxScore = session.max_score ?? session.total_steps;

  return (
    <div className="flex flex-col gap-6">
      <div className="chem-card rounded-lg p-6 text-center">
        <p className="chem-kicker">Результат</p>
        <p className="mt-2 text-4xl font-bold text-chem-royal">
          {score} / {maxScore}
        </p>
        <p className="mt-1 text-sm text-zinc-600">
          {formatSessionTitle(session)}
        </p>
      </div>

      <ul className="chem-card divide-y divide-zinc-200 rounded-lg">
        {session.steps.map((step) => (
          <li
            key={step.position}
            className="flex items-center justify-between px-4 py-3 text-sm"
          >
            <span className="text-zinc-800">
              Задание {step.type}
              {step.hint_used ? (
                <span className="ml-2 text-xs text-zinc-400">
                  (с подсказкой)
                </span>
              ) : null}
            </span>
            <span
              className={`font-semibold ${
                step.is_correct === true
                  ? "text-[var(--chem-green)]"
                  : step.is_correct === false
                    ? "text-[var(--chem-crimson)]"
                    : "text-zinc-400"
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

      <div className="flex justify-center">
        <Link
          href="/student/tests"
          className="chem-btn-primary inline-flex px-4 py-2 text-sm"
        >
          К списку тестов
        </Link>
      </div>
    </div>
  );
}
