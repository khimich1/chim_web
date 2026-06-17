"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { logout } from "@/lib/api/auth";

export function LogoutButton() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function handleLogout() {
    setBusy(true);
    try {
      await logout();
    } finally {
      router.replace("/login");
      router.refresh();
    }
  }

  return (
    <button
      type="button"
      onClick={handleLogout}
      disabled={busy}
      className="chem-btn-ghost min-h-[44px] px-3 py-2 text-sm disabled:opacity-60"
    >
      {busy ? "Выход…" : "Выйти"}
    </button>
  );
}
