import { redirect } from "next/navigation";

import { StudentNav } from "@/components/layout/StudentNav";
import { StudentOnboardingGate } from "@/components/student/StudentOnboardingGate";
import { TutorShell } from "@/components/tutor/TutorShell";
import { getCurrentUser } from "@/lib/api/server";

export default async function StudentLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }
  if (user.role !== "student") {
    redirect("/teacher");
  }
  return (
    <TutorShell>
      <StudentOnboardingGate />
      <StudentNav />
      {children}
    </TutorShell>
  );
}
