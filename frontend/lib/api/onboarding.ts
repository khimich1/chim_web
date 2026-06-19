import { apiFetch } from "@/lib/api/client";
import type { OnboardingStatus, OnboardingWelcome } from "@/lib/api/types";

export function getOnboarding(): Promise<OnboardingStatus> {
  return apiFetch<OnboardingStatus>("/api/students/me/onboarding");
}

export function getOnboardingWelcome(): Promise<OnboardingWelcome> {
  return apiFetch<OnboardingWelcome>("/api/students/me/onboarding/welcome");
}

export function patchOnboarding(payload: {
  complete_welcome?: boolean;
  mark_step?: "login" | "first_action" | "lecture";
}): Promise<OnboardingStatus> {
  return apiFetch<OnboardingStatus>("/api/students/me/onboarding", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
