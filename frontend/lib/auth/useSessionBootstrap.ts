"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuthStore } from "@/lib/auth/store";
import { onAuthLost, restoreSession } from "@/lib/auth/session-restore";

/**
 * Startup session restore (architecture.md §5.1). The in-memory access token is
 * gone after a reload, so on mount the app calls `POST /auth/refresh` once (the
 * httpOnly cookie is sent automatically). On success the store moves to
 * `authenticated`; on failure it resolves to `anonymous`. Also wires the
 * "auth lost" handler so a failed refresh-on-401 redirects to `/login` (CP-7).
 *
 * Runs the restore only while still in the pre-bootstrap `loading` state, so it
 * never clobbers a session established by login in the same browser session.
 */
export function useSessionBootstrap(): void {
  const router = useRouter();
  const status = useAuthStore((s) => s.status);
  const finishLoading = useAuthStore((s) => s.finishLoading);

  useEffect(() => {
    const unsubscribe = onAuthLost(() => {
      router.replace("/login");
    });
    return unsubscribe;
  }, [router]);

  useEffect(() => {
    if (status !== "loading") return;
    let active = true;
    void restoreSession().then((token) => {
      if (active && token === null) finishLoading();
    });
    return () => {
      active = false;
    };
  }, [status, finishLoading]);
}
