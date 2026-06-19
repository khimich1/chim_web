"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { patchOnboarding } from "@/lib/api/onboarding";
import { createSession } from "@/lib/api/tests";
import { formatFetchError } from "@/lib/api/client";
import type { RecommendedAction } from "@/lib/api/types";

function actionHref(action: RecommendedAction): string {
  if (action.kind === "homework" && action.homework_id) {
    return `/student/homework/${action.homework_id}`;
  }
  if (action.kind === "textbook") {
    return "/student/textbook";
  }
  return "/student/tests";
}

export function WelcomeActions({
  recommendedAction,
}: {
  recommendedAction: RecommendedAction;
}) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState<"start" | "skip" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function navigateToAction() {
    if (
      recommendedAction.kind === "diagnostic_test" &&
      recommendedAction.variant_ref
    ) {
      const session = await createSession(recommendedAction.variant_ref);
      router.push(`/student/tests/sessions/${session.id}`);
      return;
    }
    router.push(actionHref(recommendedAction));
  }

  async function handleStart() {
    setError(null);
    setSubmitting("start");
    try {
      await patchOnboarding({
        complete_welcome: true,
        mark_step: "first_action",
      });
      await navigateToAction();
      router.refresh();
    } catch (err) {
      setError(formatFetchError(err, "Не удалось продолжить. Попробуйте позже."));
    } finally {
      setSubmitting(null);
    }
  }

  async function handleSkip() {
    setError(null);
    setSubmitting("skip");
    try {
      await patchOnboarding({ complete_welcome: true });
      router.replace("/student");
      router.refresh();
    } catch (err) {
      setError(formatFetchError(err, "Не удалось продолжить. Попробуйте позже."));
    } finally {
      setSubmitting(null);
    }
  }

  return (
    <div className="mt-8 flex flex-col gap-3">
      <button
        type="button"
        onClick={() => void handleStart()}
        disabled={submitting !== null}
        className="chem-btn-primary min-h-[48px] px-4 py-3 text-sm font-medium disabled:opacity-60"
      >
        {submitting === "start" ? "Загрузка…" : recommendedAction.label}
      </button>
      <button
        type="button"
        onClick={() => void handleSkip()}
        disabled={submitting !== null}
        className="text-sm text-zinc-500 transition hover:text-zinc-700"
      >
        {submitting === "skip" ? "Загрузка…" : "Позже, посмотрю сам"}
      </button>
      {error ? (
        <p role="alert" className="text-sm text-[var(--chem-crimson)]">
          {error}
        </p>
      ) : null}
    </div>
  );
}
