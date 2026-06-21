"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { getUnreadCount, markNotificationRead } from "@/lib/api/notifications";
import type { Notification } from "@/lib/api/types";
import { formatHomeworkSubmittedNotification } from "@/lib/notifications/format-homework-notification";

export function NotificationBell({
  initialNotifications,
  initialUnread,
}: {
  initialNotifications: Notification[];
  initialUnread: number;
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState(initialNotifications);
  const [unread, setUnread] = useState(initialUnread);

  useEffect(() => {
    setNotifications(initialNotifications);
    setUnread(initialUnread);
  }, [initialNotifications, initialUnread]);

  useEffect(() => {
    if (!open) {
      return;
    }
    void getUnreadCount()
      .then((result) => setUnread(result.count))
      .catch(() => undefined);
  }, [open]);

  async function handleOpenNotification(notification: Notification) {
    if (!notification.read_at) {
      try {
        await markNotificationRead(notification.id);
        setNotifications((current) =>
          current.map((item) =>
            item.id === notification.id
              ? { ...item, read_at: new Date().toISOString() }
              : item,
          ),
        );
        setUnread((count) => Math.max(0, count - 1));
      } catch {
        // Non-blocking: navigation still works.
      }
    }
    setOpen(false);
    router.push(`/teacher/homework/${notification.payload.homework_id}`);
    router.refresh();
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="relative rounded-md border border-zinc-300 px-3 py-1.5 text-sm text-zinc-700 hover:bg-zinc-50"
        aria-expanded={open}
        aria-haspopup="true"
      >
        Уведомления
        {unread > 0 ? (
          <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--chem-crimson)] px-1 text-xs font-semibold text-white">
            {unread}
          </span>
        ) : null}
      </button>

      {open ? (
        <div className="absolute right-0 z-20 mt-2 w-80 rounded-lg border border-zinc-200 bg-white shadow-lg">
          <div className="border-b border-zinc-100 px-4 py-2">
            <p className="text-sm font-semibold text-zinc-900">Уведомления</p>
          </div>
          {notifications.length === 0 ? (
            <p className="px-4 py-3 text-sm text-zinc-500">Пока пусто.</p>
          ) : (
            <ul className="max-h-80 overflow-y-auto">
              {notifications.map((notification) => (
                <li key={notification.id}>
                  <button
                    type="button"
                    onClick={() => handleOpenNotification(notification)}
                    className={`w-full px-4 py-3 text-left text-sm hover:bg-zinc-50 ${
                      notification.read_at ? "text-zinc-600" : "font-medium text-zinc-900"
                    }`}
                  >
                    {formatHomeworkSubmittedNotification(notification.payload)}
                  </button>
                </li>
              ))}
            </ul>
          )}
          <div className="border-t border-zinc-100 px-4 py-2">
            <Link
              href="/teacher/notifications"
              className="chem-link text-sm"
              onClick={() => setOpen(false)}
            >
              Все уведомления
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}
