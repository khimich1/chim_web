import { apiFetch } from "@/lib/api/client";
import type { Notification, UnreadCount } from "@/lib/api/types";

export function listNotifications(): Promise<Notification[]> {
  return apiFetch<Notification[]>("/api/notifications");
}

export function getUnreadCount(): Promise<UnreadCount> {
  return apiFetch<UnreadCount>("/api/notifications/unread-count");
}

export function markNotificationRead(id: string): Promise<Notification> {
  return apiFetch<Notification>(`/api/notifications/${id}/read`, {
    method: "PATCH",
  });
}
