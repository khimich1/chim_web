"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { getOnboarding } from "@/lib/api/onboarding";
import { ApiError } from "@/lib/api/client";

export function StudentOnboardingGate() {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (pathname === "/student/welcome") {
      return;
    }

    let cancelled = false;

    async function check() {
      try {
        const status = await getOnboarding();
        if (!cancelled && status.needs_welcome) {
          router.replace("/student/welcome");
        }
      } catch (err) {
        if (cancelled || (err instanceof ApiError && err.status === 401)) {
          return;
        }
      }
    }

    void check();
    return () => {
      cancelled = true;
    };
  }, [pathname, router]);

  return null;
}
