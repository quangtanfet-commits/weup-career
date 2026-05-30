"use client";

import type { ReactNode } from "react";

import { useAuthStore } from "@/lib/auth/store";

/**
 * Authenticated route-group shell (architecture.md §3, §5.3). Client-rendered
 * so personal/sensitive data is never fetched in a Server Component (no leak
 * into the RSC cache). Full session bootstrap + route/role/consent guards are
 * layered onto this seam in the F1 auth pages and later slices; F1 ships the
 * shell and the in-memory session read.
 */
export default function AppLayout({ children }: { children: ReactNode }) {
  const status = useAuthStore((s) => s.status);

  return (
    <div className="flex min-h-screen flex-col" data-session-status={status}>
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
        {children}
      </main>
    </div>
  );
}
