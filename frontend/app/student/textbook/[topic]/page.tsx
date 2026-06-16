import Link from "next/link";
import { notFound } from "next/navigation";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { ChunkViewer } from "@/components/textbook/ChunkViewer";
import { getTextbookChunks } from "@/lib/api/server";

export default async function TextbookTopicPage({
  params,
  searchParams,
}: {
  params: Promise<{ topic: string }>;
  searchParams: Promise<{ chunk?: string }>;
}) {
  const { topic } = await params;
  const { chunk } = await searchParams;
  const decodedTopic = decodeURIComponent(topic);
  const summaries = await getTextbookChunks(decodedTopic);

  if (summaries.length === 0) {
    notFound();
  }

  const initialChunkIdx = chunk ? Number.parseInt(chunk, 10) : 0;
  const safeChunkIdx = summaries.some((item) => item.chunk_idx === initialChunkIdx)
    ? initialChunkIdx
    : summaries[0].chunk_idx;

  return (
    <main className="mx-auto max-w-5xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Учебник</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            {decodedTopic}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/student/textbook" className="chem-link text-sm">
            Все темы
          </Link>
          <LogoutButton />
        </div>
      </div>

      <section className="mt-10">
        <ChunkViewer
          topic={decodedTopic}
          summaries={summaries}
          initialChunkIdx={safeChunkIdx}
        />
      </section>
    </main>
  );
}
