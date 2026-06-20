import { LoginForm } from "@/components/auth/LoginForm";
import { BrandLogo } from "@/components/ui/BrandLogo";
import { DecorativeBlobs } from "@/components/ui/DecorativeBlobs";

interface LoginPageProps {
  searchParams: Promise<{ redirect?: string }>;
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const params = await searchParams;
  const redirectTo = params.redirect ?? null;

  return (
    <main className="relative isolate flex min-h-screen items-center justify-center px-4 py-16 sm:px-6">
      <DecorativeBlobs scoped />

      <div className="relative z-10 w-full max-w-sm">
        <div className="chem-card overflow-hidden rounded-xl">
          <header className="bg-chem-teal px-6 py-5 text-center">
            <div className="flex justify-center">
              <BrandLogo size={36} label="" />
            </div>
            <p className="mt-3 chem-kicker text-white/80">chim_web</p>
            <h1 className="mt-1 text-2xl font-semibold text-white">Вход</h1>
          </header>
          <div className="px-6 py-6 sm:px-8 sm:py-8">
            <LoginForm redirectTo={redirectTo} />
          </div>
        </div>
      </div>
    </main>
  );
}
