import { redirect } from "next/navigation";

import { TeacherNav } from "@/components/layout/TeacherNav";
import { TutorShell } from "@/components/tutor/TutorShell";
import {
  getCurrentUser,
  getNotificationUnreadCount,
  getNotifications,
} from "@/lib/api/server";

export default async function TeacherLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }
  if (user.role !== "teacher") {
    redirect("/student");
  }

  const [notifications, unread] = await Promise.all([
    getNotifications(),
    getNotificationUnreadCount(),
  ]);

  return (
    <TutorShell>
      <TeacherNav
        initialNotifications={notifications.slice(0, 5)}
        initialUnread={unread}
      />
      {children}
    </TutorShell>
  );
}
