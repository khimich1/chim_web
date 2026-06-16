import Link from "next/link";

import type { TextbookTopic } from "@/lib/api/types";

export function TopicList({ topics }: { topics: TextbookTopic[] }) {
  if (topics.length === 0) {
    return (
      <p className="text-sm text-zinc-500">
        Темы учебника недоступны. Проверьте подключение к API.
      </p>
    );
  }

  return (
    <ul className="chem-card divide-y divide-zinc-200 rounded-lg">
      {topics.map((item) => (
        <li key={item.topic}>
          <Link
            href={`/student/textbook/${encodeURIComponent(item.topic)}`}
            className="flex items-center justify-between px-4 py-3 transition hover:bg-chem-peach/20"
          >
            <span className="font-medium text-zinc-900">{item.topic}</span>
            <span className="text-sm text-zinc-500">
              {item.chunk_count}{" "}
              {item.chunk_count === 1 ? "чанк" : "чанков"}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
