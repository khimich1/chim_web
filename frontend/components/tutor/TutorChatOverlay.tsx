"use client";

import { usePathname } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { MessageBubble } from "@/components/tutor/MessageBubble";
import {
  createTutorSession,
  getTutorHealth,
  getTutorSession,
  sendTutorMessage,
  type TutorMessage,
  type TutorPageContext,
} from "@/lib/api/tutor";
import { formatFetchError } from "@/lib/api/client";
import { getSuggestedPrompts } from "@/lib/tutor/suggestedPrompts";
import { useTutorChatOptional } from "@/lib/tutor/TutorChatContext";

function buildPageContext(pathname: string): TutorPageContext {
  const textbookMatch = pathname.match(/^\/student\/textbook\/([^/]+)/);
  if (textbookMatch) {
    return { topic: decodeURIComponent(textbookMatch[1]) };
  }
  const testMatch = pathname.match(/^\/student\/tests\/sessions\/([^/]+)/);
  if (testMatch && testMatch[1] !== "summary") {
    return { test_session_id: testMatch[1] };
  }
  const homeworkMatch = pathname.match(/^\/student\/homework\/([^/]+)/);
  if (homeworkMatch) {
    return { homework_id: homeworkMatch[1] };
  }
  return {};
}

function isActiveTestSession(pathname: string): boolean {
  return /^\/student\/tests\/sessions\/[^/]+$/.test(pathname);
}

export function TutorChatOverlay() {
  const pathname = usePathname();
  const tutorChat = useTutorChatOptional();
  const routePageContext = useMemo(() => buildPageContext(pathname), [pathname]);
  const pageContext = useMemo(
    () => ({
      ...routePageContext,
      ...(tutorChat?.pageContextOverride ?? {}),
    }),
    [routePageContext, tutorChat?.pageContextOverride],
  );
  const suggestedPrompts = useMemo(
    () => getSuggestedPrompts(pageContext),
    [pageContext],
  );
  const onTestSession = isActiveTestSession(pathname);

  const [localOpen, setLocalOpen] = useState(false);
  const open = tutorChat?.open ?? localOpen;
  const setOpen = tutorChat
    ? (value: boolean) => {
        if (value) {
          tutorChat.openTutor();
        } else {
          tutorChat.closeTutor();
        }
      }
    : setLocalOpen;

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<TutorMessage[]>([]);
  const [input, setInput] = useState("");
  const [opening, setOpening] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [healthWarning, setHealthWarning] = useState<string | null>(null);

  const [trackedPathname, setTrackedPathname] = useState(pathname);
  if (pathname !== trackedPathname) {
    setTrackedPathname(pathname);
    setSessionId(null);
    setMessages([]);
    tutorChat?.clearPageContextOverride();
  }

  const ensureSession = useCallback(async () => {
    if (sessionId) return sessionId;
    const session = await createTutorSession(pageContext);
    setSessionId(session.id);
    return session.id;
  }, [pageContext, sessionId]);

  const bootstrapChat = useCallback(async () => {
    setError(null);
    setHealthWarning(null);
    setOpening(true);
    try {
      const health = await getTutorHealth();
      if (!health.openai_configured) {
        setHealthWarning(
          "OPENAI_API_KEY не задан на сервере. Ответы агента будут недоступны.",
        );
      }
      if (!health.rag_index_exists) {
        setHealthWarning(
          (prev) =>
            prev
              ? `${prev} RAG-индекс не собран — выполните: python -m app.cli.index_rag --rebuild`
              : "RAG-индекс не собран. Выполните: python -m app.cli.index_rag --rebuild",
        );
      }
      const id = await ensureSession();
      const detail = await getTutorSession(id);
      setMessages(detail.messages);
    } catch (err) {
      setError(formatFetchError(err, "Не удалось открыть чат"));
    } finally {
      setOpening(false);
    }
  }, [ensureSession]);

  const handleSendText = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || loading) return;

      setLoading(true);
      setError(null);
      setInput("");

      const optimisticUser: TutorMessage = {
        id: `tmp-${Date.now()}`,
        role: "user",
        content: trimmed,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, optimisticUser]);

      try {
        const id = await ensureSession();
        const response = await sendTutorMessage(id, trimmed);
        const assistant: TutorMessage = {
          id: response.message_id,
          role: "assistant",
          content: response.content,
          sources: response.sources,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistant]);
      } catch (err) {
        setError(formatFetchError(err, "Ошибка отправки сообщения"));
        setMessages((prev) => prev.filter((m) => m.id !== optimisticUser.id));
        setInput(trimmed);
      } finally {
        setLoading(false);
      }
    },
    [ensureSession, loading],
  );

  const handleOpen = () => {
    if (opening) return;
    setOpen(true);
  };

  useEffect(() => {
    if (!open || opening || sessionId) {
      return;
    }
    void bootstrapChat();
  }, [open, opening, sessionId, bootstrapChat]);

  useEffect(() => {
    if (!open || opening) {
      return;
    }
    const pending = tutorChat?.consumeInitialMessage();
    const autoSend = tutorChat?.consumeAutoSendInitialMessage() ?? false;
    if (pending) {
      setInput(pending);
      if (autoSend) {
        void handleSendText(pending);
      }
    }
  }, [open, opening, tutorChat, handleSendText]);

  const handleSend = async (event: React.FormEvent) => {
    event.preventDefault();
    await handleSendText(input);
  };

  const handleSuggestedPrompt = (message: string) => {
    setInput(message);
  };

  const fabPositionClass = onTestSession
    ? "bottom-36 right-4 sm:bottom-6 sm:right-6"
    : "bottom-6 right-4 sm:bottom-6 sm:right-6";

  return (
    <>
      {!open ? (
        <button
          type="button"
          onClick={handleOpen}
          disabled={opening}
          className={`fixed ${fabPositionClass} z-40 min-h-[44px] rounded-full bg-chem-teal px-4 py-3 text-sm font-medium text-white shadow-lg transition hover:bg-chem-teal-dark disabled:opacity-60`}
          aria-expanded={false}
          aria-busy={opening}
          aria-label="AI-советчик по химии"
        >
          {opening ? "Открываю…" : "AI-советчик"}
        </button>
      ) : null}

      {open ? (
        <div
          className="fixed inset-0 z-50 flex flex-col bg-white sm:inset-auto sm:bottom-20 sm:right-6 sm:left-auto sm:top-auto sm:h-[min(70vh,520px)] sm:w-[min(92vw,380px)] sm:overflow-hidden sm:rounded-xl sm:border sm:border-zinc-200 sm:shadow-2xl"
          role="dialog"
          aria-label="Чат AI-советчика"
        >
          <header className="flex items-start justify-between gap-3 border-b border-zinc-200 bg-chem-teal px-4 py-3 text-white sm:rounded-t-xl">
            <div>
              <h2 className="text-sm font-semibold">AI-советчик</h2>
              <p className="text-xs text-white/80">
                Ответы на основе учебника. Во время теста — только теория.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="chem-btn-ghost min-h-[44px] min-w-[44px] shrink-0 border-white/30 bg-white/10 px-3 py-2 text-sm text-white hover:bg-white/20"
              aria-label="Закрыть чат"
            >
              ✕
            </button>
          </header>

          <div className="flex-1 space-y-3 overflow-y-auto px-3 py-3">
            {messages.length === 0 && !opening ? (
              <div className="space-y-3">
                <p className="text-sm text-zinc-500">
                  Задайте вопрос по теории или попросите разобрать задание.
                </p>
                {suggestedPrompts.length > 0 ? (
                  <div className="flex flex-wrap gap-2" aria-label="Подсказки">
                    {suggestedPrompts.map((prompt) => (
                      <button
                        key={prompt.label}
                        type="button"
                        onClick={() => handleSuggestedPrompt(prompt.message)}
                        className="rounded-full border border-chem-teal/30 bg-chem-teal/5 px-3 py-1.5 text-xs font-medium text-chem-teal transition hover:bg-chem-teal/10"
                      >
                        {prompt.label}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : (
              messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))
            )}
            <div aria-live="polite">
              {opening ? (
                <p className="text-xs text-zinc-500">Загружаю чат…</p>
              ) : null}
              {loading ? (
                <p className="text-xs text-zinc-500">Ищу в учебнике…</p>
              ) : null}
            </div>
            {error ? (
              <p className="text-xs text-[var(--chem-crimson)]" role="alert">
                {error}
              </p>
            ) : null}
            {healthWarning ? (
              <p className="text-xs text-amber-800">{healthWarning}</p>
            ) : null}
          </div>

          <form onSubmit={handleSend} className="border-t border-zinc-200 p-3">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ваш вопрос…"
                className="chem-input min-h-[44px] flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                aria-label="Отправить"
                className="chem-btn-primary min-h-[44px] min-w-[44px] px-3 py-2 text-sm disabled:opacity-50"
              >
                →
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </>
  );
}
