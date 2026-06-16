import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 px-6 py-16">
      <div className="w-full max-w-sm rounded-xl border border-zinc-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          chim_web
        </p>
        <h1 className="mt-1 mb-6 text-2xl font-semibold text-zinc-900">Вход</h1>
        <LoginForm />
      </div>
    </main>
  );
}
