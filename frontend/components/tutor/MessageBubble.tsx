"use client";

import Link from "next/link";
import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";

import type { TutorMessage, TutorSourceCitation } from "@/lib/api/tutor";
import { sanitizeLectureText } from "@/lib/textbook/markdown";

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

const tutorMarkdownComponents: Components = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  strong: ({ children }) => (
    <strong className="font-semibold">{children}</strong>
  ),
  ul: ({ children }) => (
    <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0">{children}</ol>
  ),
  li: ({ children }) => <li>{children}</li>,
  pre: ({ children }) => (
    <pre className="my-2 overflow-x-auto rounded-md bg-zinc-100 p-2 text-xs last:mb-0">
      {children}
    </pre>
  ),
  code: ({ children, className }) => {
    if (className?.includes("language-")) {
      return <code className={className}>{children}</code>;
    }
    return (
      <code className="rounded bg-zinc-100 px-1 font-mono text-xs">
        {children}
      </code>
    );
  },
};

function AssistantMessageContent({ content }: { content: string }) {
  const safe = sanitizeLectureText(content);
  return (
    <div className="tutor-message-markdown">
      <ReactMarkdown
        components={tutorMarkdownComponents}
        rehypePlugins={[rehypeSanitize]}
      >
        {safe}
      </ReactMarkdown>
    </div>
  );
}

export function MessageBubble({ message }: { message: TutorMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isUser
            ? "bg-chem-teal text-white"
            : "chem-card border border-zinc-200 text-zinc-900"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <AssistantMessageContent content={message.content} />
        )}
        {!isUser && message.sources ? (
          <SourceList sources={message.sources} />
        ) : null}
      </div>
    </div>
  );
}
