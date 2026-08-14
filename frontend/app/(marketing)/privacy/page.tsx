import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Политика конфиденциальности | Химыч",
  description: "Обработка персональных данных на сайте Химыч.",
  robots: { index: true, follow: true },
};

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <h1 className="text-3xl font-semibold text-zinc-900">Политика конфиденциальности</h1>
      <div className="chem-card mt-8 rounded-xl p-6 text-zinc-700">
        <p>
          Отправляя заявку на сайте Химыч, вы соглашаетесь на обработку указанных персональных
          данных (имя, телефон, класс, цель обучения) исключительно для связи по вашему
          запросу и организации бесплатной диагностики. Данные не передаются третьим лицам,
          кроме случаев, предусмотренных законодательством РФ. По вопросам обработки данных
          напишите в Telegram{" "}
          <a
            href="https://t.me/himich_teacher"
            className="text-chem-teal underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            @himich_teacher
          </a>
          .
        </p>
        <p className="mt-4 text-sm text-zinc-500">
          Полный текст политики будет опубликован после юридической проработки (152-ФЗ).
        </p>
      </div>
    </div>
  );
}
