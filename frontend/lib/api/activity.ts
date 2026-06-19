import { apiFetch } from "@/lib/api/client";
import type {
  LeaderboardEntry,
  StudentStats,
  TeacherStudentStats,
} from "@/lib/api/types";

export type LeaderboardPeriod = "week" | "all_time";

/** GET /api/students/me/stats — personal gamification aggregates (Task 61). */
export function getMyStats(): Promise<StudentStats> {
  return apiFetch<StudentStats>("/api/students/me/stats");
}

/** GET /api/leaderboard — global ranking (Task 61 / Task 64). */
export function getLeaderboard(
  period: LeaderboardPeriod = "week",
  limit = 50,
): Promise<LeaderboardEntry[]> {
  const search = new URLSearchParams({
    period,
    limit: String(limit),
  });
  return apiFetch<LeaderboardEntry[]>(`/api/leaderboard?${search.toString()}`);
}

/** GET /api/teacher/students/stats — gamification metrics for teacher's students (Task 62). */
export function getTeacherStudentsStats(): Promise<TeacherStudentStats[]> {
  return apiFetch<TeacherStudentStats[]>("/api/teacher/students/stats");
}
