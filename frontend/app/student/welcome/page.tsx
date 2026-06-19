import { redirect } from "next/navigation";

import { WelcomeActions } from "@/components/student/WelcomeActions";
import { TrackExplainer } from "@/components/student/TrackExplainer";
import { DecorativeBlobs } from "@/components/ui/DecorativeBlobs";
import { getCurrentUser, getOnboardingWelcome } from "@/lib/api/server";

export default async function StudentWelcomePage() {
  const [user, welcome] = await Promise.all([
    getCurrentUser(),
    getOnboardingWelcome(),
  ]);

  if (!user) {
    redirect("/login");
  }

  if (!welcome || !welcome.needs_welcome) {
    redirect("/student");
  }

  const track = user.track ?? "ege";

  return (
    <main className="relative isolate mx-auto flex min-h-[70vh] max-w-lg items-center px-4 py-12 sm:px-6">
      <DecorativeBlobs scoped />

      <div className="chem-card relative z-10 w-full rounded-xl p-6 sm:p-8">
        <p className="chem-kicker">Добро пожаловать</p>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-900">
          {user.email}
        </h1>

        <div className="mt-5">
          <TrackExplainer track={track} />
        </div>

        <p className="mt-6 text-sm leading-relaxed text-zinc-600">
          Здесь между занятиями ты будешь делать домашние задания, слушать
          лекции и проходить тесты в формате экзамена.
        </p>

        <WelcomeActions recommendedAction={welcome.recommended_action} />
      </div>
    </main>
  );
}
