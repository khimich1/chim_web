import { redirect } from "next/navigation";

import { TutorChatOverlay } from "@/components/tutor/TutorChatOverlay";
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
      {children}
      <TutorChatOverlay />
    </>
  );
}
