import Link from "next/link";

const VK_URL = "https://vk.ru/himich_teachr24";
const TG_URL = "https://t.me/himich_teacher";

export function MarketingFooter() {
  return (
    <footer className="mt-auto border-t border-chem-teal/10 bg-chem-surface-muted">
      <div className="mx-auto flex max-w-5xl flex-col gap-4 px-4 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <a
            href={VK_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-chem-teal-dark hover:text-chem-teal"
          >
            ВКонтакте
          </a>
          <a
            href={TG_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-chem-teal-dark hover:text-chem-teal"
          >
            Telegram
          </a>
          <Link href="/privacy" className="text-zinc-600 hover:text-chem-teal-dark">
            Политика конфиденциальности
          </Link>
        </div>
        <p className="text-sm text-zinc-500">© {new Date().getFullYear()} Химыч</p>
      </div>
    </footer>
  );
}
