import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { NotificationBell } from "@/components/notifications/NotificationBell";
import { HomeworkList } from "@/components/homework/HomeworkList";
import {
  getCurrentUser,
  getHomeworkList,
  getNotificationUnreadCount,
  getNotifications,
} from "@/lib/api/server";

export default async function TeacherHomeworkPage() {
  const [user, homework, notifications, unread] = await Promise.all([
    getCurrentUser(),
    getHomeworkList(),
    getNotifications(),
    getNotificationUnreadCount(),
  ]);

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Кабинет преподавателя</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            Домашние задания
          </h1>
          <p className="mt-1 text-sm text-zinc-600">{user?.email}</p>
        </div>
        <div className="flex items-center gap-3">
          <NotificationBell
            initialNotifications={notifications}
            initialUnread={unread}
          />
          <Link href="/teacher" className="chem-link text-sm">
            На главную
          </Link>
          <LogoutButton />
        </div>
      </div>

      <div className="mt-6">
        <Link
          href="/teacher/homework/new"
          className="chem-btn-primary inline-flex px-4 py-2 text-sm"
        >
          Создать задание
        </Link>
      </div>

      <section className="mt-10">
        <HomeworkList assignments={homework} detailBasePath="/teacher/homework" />
      </section>
    </main>
  );
}
