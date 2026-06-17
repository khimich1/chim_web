import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";

import { Callout } from "@/components/textbook/Callout";
import { Formula } from "@/components/textbook/Formula";
import { parseLectureSegments } from "@/lib/textbook/markdown";

const markdownComponents: Components = {
  h1: ({ children }) => (
    <h1 className="mb-4 mt-2 text-2xl font-bold text-zinc-900">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="mb-4 mt-8 first:mt-0">
      <span className="chem-section-pill">{children}</span>
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="mb-3 mt-6 text-lg font-semibold text-zinc-900">{children}</h3>
  ),
  p: ({ children }) => <p className="mb-3">{children}</p>,
  ul: ({ children }) => (
    <ul className="mb-3 list-disc space-y-1 pl-6">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="mb-3 list-decimal space-y-1 pl-6">{children}</ol>
  ),
  code: ({ children, className }) => {
    if (className?.includes("language-")) {
      return <code className={className}>{children}</code>;
    }
    return <Formula>{children}</Formula>;
  },
};

function MarkdownBlock({ content }: { content: string }) {
  return (
    <ReactMarkdown components={markdownComponents}>{content}</ReactMarkdown>
  );
}

export function LectureContent({ lecture }: { lecture: string }) {
  const segments = parseLectureSegments(lecture);

  return (
    <div className="chem-lecture-prose text-zinc-800">
      {segments.map((segment, index) => {
        if (segment.type === "callout") {
          return (
            <Callout key={`callout-${index}`} variant={segment.variant}>
              <MarkdownBlock content={segment.content} />
            </Callout>
          );
        }
        return <MarkdownBlock key={`md-${index}`} content={segment.content} />;
      })}
    </div>
  );
}
