import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { TopicList } from "@/components/textbook/TopicList";
import { getTextbookTopics } from "@/lib/api/server";

export default async function TextbookPage() {
  const topics = await getTextbookTopics();

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Кабинет ученика</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">Учебник</h1>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/student" className="chem-link text-sm">
            На главную
          </Link>
          <LogoutButton />
        </div>
      </div>

      <section className="mt-10">
        <TopicList topics={topics} />
      </section>
    </main>
  );
}
