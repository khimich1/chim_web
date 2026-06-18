import { redirect } from "next/navigation";

import { TeacherNav } from "@/components/layout/TeacherNav";
import { TutorShell } from "@/components/tutor/TutorShell";
import { getCurrentUser } from "@/lib/api/server";

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
  return (
    <TutorShell>
      <TeacherNav />
      {children}
    </TutorShell>
  );
}
