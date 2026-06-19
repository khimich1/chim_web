import { TrackBadge } from "@/components/ui/TrackBadge";
import { resolvePublicDisplayName } from "@/lib/activity/display-name";
import { formatTotalMinutes } from "@/lib/format-duration";
import type { Student, TeacherStudentStats } from "@/lib/api/types";

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
  }).format(new Date(iso));
}

function formatActiveDate(iso: string | null): string {
  if (!iso) {
    return "—";
  }
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
  }).format(new Date(iso));
}

export function StudentList({
  students,
  stats = [],
}: {
  students: Student[];
  stats?: TeacherStudentStats[];
}) {
  const statsById = new Map(stats.map((row) => [row.id, row]));
  const showStats = stats.length > 0;

  if (students.length === 0) {
    return (
      <p className="text-sm text-zinc-500">Пока нет учеников. Создайте первого.</p>
    );
  }

  return (
    <div className="chem-card overflow-x-auto rounded-lg">
      <table className="w-full min-w-[40rem] text-left text-sm">
        <thead className="chem-table-head">
          <tr>
            <th className="px-4 py-3 font-medium">Ученик</th>
            <th className="px-4 py-3 font-medium">Трек</th>
            <th className="px-4 py-3 font-medium">Онбординг</th>
            {showStats ? (
              <>
                <th className="px-4 py-3 font-medium">Баллы (нед.)</th>
                <th className="px-4 py-3 font-medium">Streak</th>
                <th className="px-4 py-3 font-medium">Задач</th>
                <th className="px-4 py-3 font-medium">Время</th>
                <th className="px-4 py-3 font-medium">Активность</th>
              </>
            ) : (
              <th className="px-4 py-3 font-medium">Создан</th>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-200">
          {students.map((student) => {
            const row = statsById.get(student.id);

            return (
              <tr key={student.id}>
                <td className="px-4 py-3">
                  <div className="text-zinc-900">
                    {resolvePublicDisplayName(
                      row?.display_name ?? null,
                      student.id,
                    )}
                  </div>
                  <div className="text-xs text-zinc-500">{student.email}</div>
                </td>
                <td className="px-4 py-3">
                  <TrackBadge track={student.track} />
                </td>
                <td className="px-4 py-3">
                  {student.is_activated ? (
                    <span className="text-sm font-medium text-chem-teal-dark">
                      Активен
                    </span>
                  ) : (
                    <span className="text-sm text-zinc-500">Не активирован</span>
                  )}
                </td>
                {showStats ? (
                  <>
                    <td className="px-4 py-3 text-zinc-900">
                      {row?.week_points ?? 0}
                      <span className="text-xs text-zinc-500">
                        {" "}
                        / {row?.total_points ?? 0}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-zinc-900">
                      {row?.streak ?? 0}
                    </td>
                    <td className="px-4 py-3 text-zinc-900">
                      {row?.tasks_solved ?? 0}
                    </td>
                    <td className="px-4 py-3 text-zinc-900">
                      {formatTotalMinutes(row?.total_minutes ?? 0)}
                    </td>
                    <td className="px-4 py-3 text-zinc-500">
                      {formatActiveDate(row?.last_active_date ?? null)}
                    </td>
                  </>
                ) : (
                  <td className="px-4 py-3 text-zinc-500">
                    {formatDate(student.created_at)}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
