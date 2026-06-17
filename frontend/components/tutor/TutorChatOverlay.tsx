"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useMemo, useState } from "react";

import {
  createTutorSession,
  getTutorHealth,
  getTutorSession,
  sendTutorMessage,
  type TutorMessage,
  type TutorPageContext,
  type TutorSourceCitation,
} from "@/lib/api/tutor";
import { formatFetchError } from "@/lib/api/client";

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

function SourceList({ sources }: { sources: TutorSourceCitation[] }) {
  if (!sources.length) return null;
  return (
    <ul className="mt-2 space-y-1 text-xs text-zinc-600">
      {sources.map((source, index) => (
        <li key={`${source.topic}-${source.chunk_idx}-${index}`}>
          {source.topic && source.chunk_title ? (
            <Link
              href={`/student/textbook/${encodeURIComponent(source.topic)}`}
              className="chem-link"
            >
              {source.topic} → {source.chunk_title}
            </Link>
          ) : (
            <span>{source.topic ?? "Источник"}</span>
          )}
        </li>
      ))}
    </ul>
  );
}

function MessageBubble({ message }: { message: TutorMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isUser
            ? "bg-blue-600 text-white"
            : "border border-zinc-200 bg-white text-zinc-900"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {!isUser && message.sources ? (
          <SourceList sources={message.sources} />
        ) : null}
      </div>
    </div>
  );
}

export function TutorChatOverlay() {
  const pathname = usePathname();
  const pageContext = useMemo(() => buildPageContext(pathname), [pathname]);

  const [open, setOpen] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<TutorMessage[]>([]);
  const [input, setInput] = useState("");
  const [opening, setOpening] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [healthWarning, setHealthWarning] = useState<string | null>(null);

  // I1: page_context is derived from the route. When the route changes the
  // cached sessionId would otherwise pin a stale context (e.g. textbook topic
  // while the student is now on a test). Reset during render (React's
  // "adjust state on prop change" pattern) so the next open/send creates a
  // fresh session with the current page_context.
  const [trackedPathname, setTrackedPathname] = useState(pathname);
  if (pathname !== trackedPathname) {
    setTrackedPathname(pathname);
    setSessionId(null);
    setMessages([]);
  }

  const ensureSession = useCallback(async () => {
    if (sessionId) return sessionId;
    const session = await createTutorSession(pageContext);
    setSessionId(session.id);
    return session.id;
  }, [pageContext, sessionId]);

  const handleOpen = async () => {
    if (opening) return; // I6: guard against double-click
    setOpen(true);
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
  };

  const handleSend = async (event: React.FormEvent) => {
    event.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setLoading(true);
    setError(null);
    setInput("");

    const optimisticUser: TutorMessage = {
      id: `tmp-${Date.now()}`,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUser]);

    try {
      const id = await ensureSession();
      const response = await sendTutorMessage(id, text);
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
      setInput(text);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => (open ? setOpen(false) : handleOpen())}
        disabled={opening}
        className="fixed bottom-6 right-6 z-40 rounded-full bg-blue-600 px-4 py-3 text-sm font-medium text-white shadow-lg hover:bg-blue-700 disabled:opacity-60"
        aria-expanded={open}
        aria-busy={opening}
        aria-label="AI-советчик по химии"
      >
        {opening ? "Открываю…" : open ? "Свернуть чат" : "AI-советчик"}
      </button>

      {open ? (
        <div
          className="fixed bottom-20 right-6 z-40 flex h-[min(70vh,520px)] w-[min(92vw,380px)] flex-col overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-2xl"
          role="dialog"
          aria-label="Чат AI-советчика"
        >
          <header className="border-b border-zinc-200 px-4 py-3">
            <h2 className="text-sm font-semibold text-zinc-900">AI-советчик</h2>
            <p className="text-xs text-zinc-500">
              Ответы на основе учебника. Во время теста — только теория.
            </p>
          </header>

          <div className="flex-1 space-y-3 overflow-y-auto px-3 py-3">
            {messages.length === 0 && !opening ? (
              <p className="text-sm text-zinc-500">
                Задайте вопрос по теории или попросите разобрать задание.
              </p>
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
              <p className="text-xs text-red-600" role="alert">
                {error}
              </p>
            ) : null}
            {healthWarning ? (
              <p className="text-xs text-amber-700">{healthWarning}</p>
            ) : null}
          </div>

          <form onSubmit={handleSend} className="border-t border-zinc-200 p-3">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ваш вопрос…"
                className="flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="rounded-md bg-blue-600 px-3 py-2 text-sm text-white disabled:opacity-50"
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
