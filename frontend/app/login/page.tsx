import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-16">
      <div className="chem-card w-full max-w-sm rounded-xl p-8">
        <p className="chem-kicker">chim_web</p>
        <h1 className="mt-1 mb-6 text-2xl font-semibold text-zinc-900">Вход</h1>
        <LoginForm />
      </div>
    </main>
  );
}
