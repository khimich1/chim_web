"use client";

import type { ReactNode } from "react";

import { TutorChatOverlay } from "@/components/tutor/TutorChatOverlay";
import { TutorChatProvider } from "@/lib/tutor/TutorChatContext";

export function TutorShell({ children }: { children: ReactNode }) {
  return (
    <TutorChatProvider>
      {children}
      <TutorChatOverlay />
    </TutorChatProvider>
  );
}
