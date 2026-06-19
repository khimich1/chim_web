"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { formatFetchError } from "@/lib/api/client";
import { getSession, getActiveSession } from "@/lib/api/tests";
import type { HomeworkAssignment, TestVariant } from "@/lib/api/types";
import { formatSessionTitle } from "@/components/tests/session-utils";
import { formatElapsedSince } from "@/lib/format-duration";

interface ResumeCard {
  sessionId: string;
  title: string;
  subtitle: string | null;
  createdAt: string;
  answeredSteps: number;
  totalSteps: number;
}

function buildHomeworkCandidates(
  homework: HomeworkAssignment[],
): Array<{ sessionId: string; title: string }> {
  return homework
    .filter((item) => item.active_test_session_id)
    .map((item) => ({
      sessionId: item.active_test_session_id as string,
      title: item.title,
    }));
}

export function ResumeSessionCards({
  homework,
  variants = [],
}: {
  homework: HomeworkAssignment[];
  variants?: TestVariant[];
}) {
  const router = useRouter();
  const [cards, setCards] = useState<ResumeCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(() => new Date());

  const homeworkCandidates = useMemo(
    () => buildHomeworkCandidates(homework),
    [homework],
  );
  const variantFilenames = useMemo(
    () => variants.map((variant) => variant.filename),
    [variants],
  );

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const seen = new Set<string>();
        const loaded: ResumeCard[] = [];

        for (const candidate of homeworkCandidates) {
          if (seen.has(candidate.sessionId)) {
            continue;
          }
          const session = await getSession(candidate.sessionId);
          if (session.status !== "in_progress") {
            continue;
          }
          seen.add(session.id);
          loaded.push({
            sessionId: session.id,
            title: candidate.title,
            subtitle: formatSessionTitle(session),
            createdAt: session.created_at ?? new Date().toISOString(),
            answeredSteps: session.steps.filter(
              (step) => step.status !== "unseen",
            ).length,
            totalSteps: session.total_steps,
          });
        }

        for (const filename of variantFilenames) {
          const active = await getActiveSession({ variantRef: filename });
          if (!active.session_id || seen.has(active.session_id)) {
            continue;
          }
          const session = await getSession(active.session_id);
          if (session.status !== "in_progress" || session.homework_assignment_id) {
            continue;
          }
          seen.add(session.id);
          loaded.push({
            sessionId: session.id,
            title: formatSessionTitle(session),
            subtitle: "Свободная практика",
            createdAt: session.created_at ?? new Date().toISOString(),
            answeredSteps: session.steps.filter(
              (step) => step.status !== "unseen",
            ).length,
            totalSteps: session.total_steps,
          });
        }

        if (!cancelled) {
          setCards(loaded);
        }
      } catch (err) {
        if (!cancelled) {
          setError(formatFetchError(err, "Не удалось загрузить сессии"));
          setCards([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [homeworkCandidates, variantFilenames]);

  if (loading) {
    return (
      <section aria-labelledby="resume-sessions-heading" className="mt-8">
        <h2 id="resume-sessions-heading" className="chem-kicker">
          Продолжить
        </h2>
        <p className="mt-3 text-sm text-zinc-500" aria-live="polite">
          Загрузка…
        </p>
      </section>
    );
  }

  if (error) {
    return (
      <section aria-labelledby="resume-sessions-heading" className="mt-8">
        <h2 id="resume-sessions-heading" className="chem-kicker">
          Продолжить
        </h2>
        <p className="mt-3 text-sm text-text-negative" role="alert">
          {error}
        </p>
      </section>
    );
  }

  if (cards.length === 0) {
    return null;
  }

  return (
    <section aria-labelledby="resume-sessions-heading" className="mt-8">
      <h2 id="resume-sessions-heading" className="chem-kicker">
        Продолжить
      </h2>
      <ul className="mt-4 flex flex-col gap-4">
        {cards.map((card) => (
          <li key={card.sessionId} className="chem-card overflow-hidden rounded-xl">
            <div className="flex flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-5">
              <div className="min-w-0">
                <h3 className="text-base font-semibold text-zinc-900">{card.title}</h3>
                {card.subtitle ? (
                  <p className="mt-0.5 text-sm text-zinc-600">{card.subtitle}</p>
                ) : null}
                <p className="mt-2 text-sm text-zinc-500">
                  Прошло {formatElapsedSince(card.createdAt, now)} ·{" "}
                  {card.answeredSteps} / {card.totalSteps} шагов
                </p>
              </div>
              <button
                type="button"
                className="chem-btn-primary shrink-0 self-start sm:self-center"
                onClick={() =>
                  router.push(`/student/tests/sessions/${card.sessionId}`)
                }
              >
                Продолжить
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
