"use client";

import { useEffect } from "react";

import { patchOnboarding } from "@/lib/api/onboarding";
import { ApiError } from "@/lib/api/client";

export function MarkOnboardingStep({
  step,
}: {
  step: "lecture";
}) {
  useEffect(() => {
    let cancelled = false;

    async function mark() {
      try {
        await patchOnboarding({ mark_step: step });
      } catch (err) {
        if (!cancelled && !(err instanceof ApiError && err.status === 401)) {
          // Non-blocking: checklist is a nice-to-have indicator.
        }
      }
    }

    void mark();
    return () => {
      cancelled = true;
    };
  }, [step]);

  return null;
}
