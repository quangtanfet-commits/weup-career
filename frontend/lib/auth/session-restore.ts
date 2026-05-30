"use client";

import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { useAuthStore } from "@/lib/auth/store";

/**
 * Session restore + "auth lost" plumbing (architecture.md §5.1/§5.2, CP-7).
 *
 * Two callers share one single-flight refresh:
 *  - **Startup bootstrap** — the in-memory access token is gone after a reload,
 *    so the app calls `restoreSession()` once on mount; the httpOnly refresh
 *    cookie is sent automatically.
 *  - **Refresh-on-401 interceptor** (`lib/api/client.ts`) — a 401 on any authed
 *    call triggers `restoreSession()`, then retries the original request once.
 *
 * Single-flight: concurrent callers await the SAME in-flight promise so a burst
 * of 401s causes exactly one `POST /auth/refresh` (no refresh storm).
 */
type TokenResponse = components["schemas"]["TokenResponse"];

let inFlight: Promise<string | null> | null = null;

/** Handlers invoked when the session is irrecoverably lost (redirect to login). */
const authLostHandlers = new Set<() => void>();

/**
 * Register a callback to run when the session is lost (e.g. router push to
 * `/login`). Returns an unsubscribe fn for cleanup on unmount.
 */
export function onAuthLost(handler: () => void): () => void {
  authLostHandlers.add(handler);
  return () => authLostHandlers.delete(handler);
}

/**
 * Clear the in-memory session and notify listeners. Called by the interceptor
 * when a refresh attempt fails (CP-7: revoked refresh token → 401 → logout).
 */
export function notifyAuthLost(): void {
  useAuthStore.getState().clearSession();
  for (const handler of authLostHandlers) handler();
}

/**
 * Attempt to (re)establish a session from the refresh cookie. Resolves to the
 * fresh access token on success, or `null` if the user is not authenticated.
 * Concurrent calls coalesce into one network request.
 */
export function restoreSession(): Promise<string | null> {
  if (inFlight) return inFlight;

  inFlight = (async () => {
    try {
      const data = await apiFetch<TokenResponse>("/auth/refresh", {
        method: "POST",
        skipAuthRefresh: true,
      });
      useAuthStore.getState().setSessionFromToken(data.access_token, data.user);
      return data.access_token;
    } catch {
      // No valid cookie / revoked token: treat as anonymous, do not throw.
      return null;
    } finally {
      inFlight = null;
    }
  })();

  return inFlight;
}

/** Test-only: reset the in-flight latch so each case starts clean. */
export function __resetSessionRestoreForTests(): void {
  inFlight = null;
  authLostHandlers.clear();
}
