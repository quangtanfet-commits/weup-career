"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

import { useAuthStore } from "@/lib/auth/store";
import { useSessionBootstrap } from "@/lib/auth/useSessionBootstrap";

/**
 * Authenticated route-group shell + route guard (architecture.md §3, §5.1/§5.3).
 * Client-rendered so personal/sensitive data is never fetched in a Server
 * Component (no leak into the RSC cache).
 *
 * `useSessionBootstrap()` runs the silent startup refresh once. While the
 * session is still `loading` (or once it resolves to `anonymous` and we are
 * redirecting), no protected children are rendered — only when `authenticated`.
 * An anonymous result triggers a single `replace("/login")` (CP-7 dead-end
 * avoidance). The backend stays the final authority on every request.
 */
export default function AppLayout({ children }: { children: ReactNode }) {
  useSessionBootstrap();
  const t = useTranslations("common");
  const router = useRouter();
  const status = useAuthStore((s) => s.status);

  useEffect(() => {
    if (status === "anonymous") {
      router.replace("/login");
    }
  }, [status, router]);

  if (status !== "authenticated") {
    return (
      <div
        className="flex min-h-screen items-center justify-center px-4"
        data-session-status={status}
      >
        <p role="status" className="text-sm text-ink-600">
          {t("loading")}
        </p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col" data-session-status={status}>
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
        {children}
      </main>
    </div>
  );
}
