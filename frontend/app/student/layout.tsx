import { redirect } from "next/navigation";

import { StudentNav } from "@/components/layout/StudentNav";
import { StudentOnboardingGate } from "@/components/student/StudentOnboardingGate";
import { TutorShell } from "@/components/tutor/TutorShell";
import { DecorativeBlobs } from "@/components/ui/DecorativeBlobs";
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
    <>
      <DecorativeBlobs />
      <TutorShell>
      <StudentOnboardingGate />
      <StudentNav />
      {children}
    </TutorShell>
    </>
  );
}
