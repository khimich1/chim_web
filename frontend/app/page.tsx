export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 px-6 py-16">
      <div className="w-full max-w-lg rounded-xl border border-zinc-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          chim_web
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-zinc-900">
          Chemistry
        </h1>
        <p className="mt-4 text-zinc-600">
          Платформа для репетитора по химии и учеников. Скелет приложения
          готов — дальше auth, учебник, тесты и домашние задания.
        </p>
        <p className="mt-6 text-sm text-zinc-500">
          API:{" "}
          <code className="rounded bg-zinc-100 px-1.5 py-0.5 text-zinc-700">
            {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
          </code>
        </p>
      </div>
    </main>
  );
}
