import { LoginForm } from "@/components/auth/LoginForm";
import { BrandLogo } from "@/components/ui/BrandLogo";
import { DecorativeBlobs } from "@/components/ui/DecorativeBlobs";

export default function LoginPage() {
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
            <LoginForm />
          </div>
        </div>
      </div>
    </main>
  );
}
