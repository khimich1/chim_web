import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { getNotifications } from "@/lib/api/server";

export default async function TeacherNotificationsPage() {
  const notifications = await getNotifications();

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Кабинет преподавателя</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            Уведомления
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/teacher" className="chem-link text-sm">
            На главную
          </Link>
          <LogoutButton />
        </div>
      </div>

      <section className="mt-10">
        {notifications.length === 0 ? (
          <p className="text-sm text-zinc-500">Уведомлений пока нет.</p>
        ) : (
          <ul className="chem-card divide-y divide-zinc-200 rounded-lg">
            {notifications.map((notification) => (
              <li key={notification.id} className="px-4 py-4">
                <Link
                  href={`/teacher/homework/${notification.payload.homework_id}`}
                  className={`block text-sm ${
                    notification.read_at
                      ? "text-zinc-600"
                      : "font-medium text-zinc-900"
                  }`}
                >
                  {notification.payload.student_email} сдал(а) «
                  {notification.payload.homework_title}»
                </Link>
                <p className="mt-1 text-xs text-zinc-500">
                  {new Date(notification.created_at).toLocaleString("ru-RU")}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
