import { redirect } from "next/navigation";

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
  return <>{children}</>;
}
