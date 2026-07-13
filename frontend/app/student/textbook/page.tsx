import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { SectionPills } from "@/components/textbook/SectionPills";
import { TopicList } from "@/components/textbook/TopicList";
import { getTextbookSections, getTextbookTopics } from "@/lib/api/server";

const DEFAULT_SECTION = "basics";

export default async function TextbookPage({
  searchParams,
}: {
  searchParams: Promise<{ section?: string }>;
}) {
  const { section: sectionParam } = await searchParams;
  const sections = await getTextbookSections();
  const knownSectionIds = new Set(sections.map((item) => item.section_id));
  const activeSection =
    sectionParam && knownSectionIds.has(sectionParam)
      ? sectionParam
      : (sections[0]?.section_id ?? DEFAULT_SECTION);
  const topics = await getTextbookTopics(activeSection);

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

      <section className="mt-8">
        <SectionPills sections={sections} activeSection={activeSection} />
      </section>

      <section className="mt-6">
        <TopicList topics={topics} section={activeSection} />
      </section>
    </main>
  );
}
