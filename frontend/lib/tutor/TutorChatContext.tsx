"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { TutorPageContext } from "@/lib/api/tutor";

export type OpenTutorOptions = {
  pageContext?: TutorPageContext;
  initialMessage?: string;
  autoSendInitialMessage?: boolean;
};

type TutorChatContextValue = {
  open: boolean;
  pageContextOverride: TutorPageContext | null;
  initialMessage: string | null;
  autoSendInitialMessage: boolean;
  openTutor: (options?: OpenTutorOptions) => void;
  closeTutor: () => void;
  consumeInitialMessage: () => string | null;
  consumeAutoSendInitialMessage: () => boolean;
  clearPageContextOverride: () => void;
};

const TutorChatContext = createContext<TutorChatContextValue | null>(null);

export function TutorChatProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [pageContextOverride, setPageContextOverride] =
    useState<TutorPageContext | null>(null);
  const [initialMessage, setInitialMessage] = useState<string | null>(null);
  const [autoSendInitialMessage, setAutoSendInitialMessage] = useState(false);

  const openTutor = useCallback((options?: OpenTutorOptions) => {
    setPageContextOverride(options?.pageContext ?? null);
    setInitialMessage(options?.initialMessage?.trim() || null);
    setAutoSendInitialMessage(Boolean(options?.autoSendInitialMessage));
    setOpen(true);
  }, []);

  const closeTutor = useCallback(() => {
    setOpen(false);
  }, []);

  const consumeInitialMessage = useCallback(() => {
    const message = initialMessage;
    setInitialMessage(null);
    return message;
  }, [initialMessage]);

  const consumeAutoSendInitialMessage = useCallback(() => {
    const shouldSend = autoSendInitialMessage;
    setAutoSendInitialMessage(false);
    return shouldSend;
  }, [autoSendInitialMessage]);

  const clearPageContextOverride = useCallback(() => {
    setPageContextOverride(null);
  }, []);

  const value = useMemo(
    () => ({
      open,
      pageContextOverride,
      initialMessage,
      autoSendInitialMessage,
      openTutor,
      closeTutor,
      consumeInitialMessage,
      consumeAutoSendInitialMessage,
      clearPageContextOverride,
    }),
    [
      open,
      pageContextOverride,
      initialMessage,
      autoSendInitialMessage,
      openTutor,
      closeTutor,
      consumeInitialMessage,
      consumeAutoSendInitialMessage,
      clearPageContextOverride,
    ],
  );

  return (
    <TutorChatContext.Provider value={value}>{children}</TutorChatContext.Provider>
  );
}

export function useTutorChat(): TutorChatContextValue {
  const context = useContext(TutorChatContext);
  if (!context) {
    throw new Error("useTutorChat must be used within TutorChatProvider");
  }
  return context;
}

export function useTutorChatOptional(): TutorChatContextValue | null {
  return useContext(TutorChatContext);
}
