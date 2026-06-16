import { TrackBadge } from "@/components/ui/TrackBadge";
import type { Student } from "@/lib/api/types";

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
  }).format(new Date(iso));
}

export function StudentList({ students }: { students: Student[] }) {
  if (students.length === 0) {
    return (
      <p className="text-sm text-zinc-500">Пока нет учеников. Создайте первого.</p>
    );
  }

  return (
    <div className="chem-card overflow-hidden rounded-lg">
      <table className="w-full text-left text-sm">
        <thead className="chem-table-head">
          <tr>
            <th className="px-4 py-3 font-medium">Email</th>
            <th className="px-4 py-3 font-medium">Трек</th>
            <th className="px-4 py-3 font-medium">Создан</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-200">
          {students.map((student) => (
            <tr key={student.id}>
              <td className="px-4 py-3 text-zinc-900">{student.email}</td>
              <td className="px-4 py-3">
                <TrackBadge track={student.track} />
              </td>
              <td className="px-4 py-3 text-zinc-500">
                {formatDate(student.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
