export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6 py-16">
      <div className="chem-card w-full max-w-lg rounded-xl p-8">
        <p className="chem-kicker">chim_web</p>
        <h1 className="mt-2 text-3xl font-semibold text-zinc-900">
          Химия
        </h1>
        <p className="mt-4 text-zinc-600">
          Платформа для репетитора по химии и учеников.
        </p>
        <p className="mt-6 text-sm text-zinc-500">
          API:{" "}
          <code className="rounded bg-chem-peach/30 px-1.5 py-0.5 text-zinc-700">
            {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
          </code>
        </p>
        <a href="/login" className="chem-btn-primary mt-6 inline-block px-4 py-2 text-sm">
          Войти
        </a>
      </div>
    </main>
  );
}
