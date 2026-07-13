import Link from "next/link";

import type { TextbookTopic } from "@/lib/api/types";

export function TopicList({
  topics,
  section,
}: {
  topics: TextbookTopic[];
  section?: string;
}) {
  if (topics.length === 0) {
    return (
      <p className="text-sm text-zinc-500">
        В этом разделе пока нет тем.
      </p>
    );
  }

  return (
    <ul className="chem-card divide-y divide-zinc-200 rounded-lg">
      {topics.map((item) => {
        const href = section
          ? `/student/textbook/${encodeURIComponent(item.topic)}?section=${encodeURIComponent(section)}`
          : `/student/textbook/${encodeURIComponent(item.topic)}`;

        return (
          <li key={item.topic}>
            <Link
              href={href}
              className="flex items-center justify-between px-4 py-3 transition hover:bg-chem-peach/20"
            >
              <span className="font-medium text-zinc-900">{item.topic}</span>
              <span className="text-sm text-zinc-500">
                {item.chunk_count}{" "}
                {item.chunk_count === 1 ? "чанк" : "чанков"}
              </span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
