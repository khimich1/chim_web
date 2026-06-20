import Link from "next/link";

import { LogoutButton } from "@/components/auth/LogoutButton";
import { NotificationBell } from "@/components/notifications/NotificationBell";
import {
  getCurrentUser,
  getHomeworkList,
  getNotificationUnreadCount,
  getNotifications,
  getStudents,
} from "@/lib/api/server";

export default async function TeacherDashboard() {
  const [user, students, homework, notifications, unread] = await Promise.all([
    getCurrentUser(),
    getStudents(),
    getHomeworkList(),
    getNotifications(),
    getNotificationUnreadCount(),
  ]);

  const activeHomework = homework.filter((item) => item.status !== "submitted").length;

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="chem-kicker">Кабинет преподавателя</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-900">
            {user?.email}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <NotificationBell
            initialNotifications={notifications.slice(0, 5)}
            initialUnread={unread}
          />
          <LogoutButton />
        </div>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <div className="chem-card rounded-lg p-4">
          <p className="text-sm text-zinc-500">Ученики</p>
          <p className="mt-1 text-2xl font-semibold text-zinc-900">
            {students.length}
          </p>
        </div>
        <div className="chem-card rounded-lg p-4">
          <p className="text-sm text-zinc-500">Активные ДЗ</p>
          <p className="mt-1 text-2xl font-semibold text-zinc-900">
            {activeHomework}
          </p>
        </div>
        <div className="chem-card rounded-lg p-4">
          <p className="text-sm text-zinc-500">Непрочитанные</p>
          <p className="mt-1 text-2xl font-semibold text-zinc-900">{unread}</p>
        </div>
      </div>

      <div className="mt-8 flex flex-wrap gap-3">
        <Link href="/teacher/students" className="chem-btn-primary inline-flex px-4 py-2 text-sm">
          Ученики
        </Link>
        <Link
          href="/teacher/homework"
          className="inline-flex rounded-md border border-chem-royal px-4 py-2 text-sm font-medium text-chem-royal transition hover:bg-chem-royal/5"
        >
          Домашние задания
        </Link>
        <Link
          href="/teacher/notifications"
          className="inline-flex rounded-md border border-chem-royal px-4 py-2 text-sm font-medium text-chem-royal transition hover:bg-chem-royal/5"
        >
          Уведомления
        </Link>
        <Link
          href="/teacher/tutor"
          className="inline-flex rounded-md border border-chem-royal px-4 py-2 text-sm font-medium text-chem-royal transition hover:bg-chem-royal/5"
        >
          AI-советчик
        </Link>
        <Link
          href="/teacher/themes"
          className="inline-flex rounded-md border border-chem-royal px-4 py-2 text-sm font-medium text-chem-royal transition hover:bg-chem-royal/5"
        >
          Конструктор тем
        </Link>
      </div>
    </main>
  );
}
