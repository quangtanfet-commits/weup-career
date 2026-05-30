"use client";

import { create } from "zustand";

/**
 * Authenticated user as surfaced by `/auth/me` / login payload
 * (architecture.md §5.3). Kept minimal in F1; later slices widen it as feature
 * pages need more claims.
 */
export interface SessionUser {
  readonly id: string;
  readonly email: string;
  readonly roles: readonly string[];
  readonly age_band?: string;
  readonly account_status?: string;
}

export type SessionStatus = "anonymous" | "authenticated";

interface AuthState {
  /**
   * Access token held **in memory only** (architecture.md §5.1). It is never
   * persisted to localStorage/cookies and never placed in a server-rendered
   * cache, which keeps sensitive data out of RSC output and shrinks the XSS
   * surface. There is deliberately no `persist` middleware here.
   */
  accessToken: string | null;
  user: SessionUser | null;
  status: SessionStatus;
  setSession: (token: string, user: SessionUser) => void;
  clearSession: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  status: "anonymous",
  setSession: (accessToken, user) =>
    set({ accessToken, user, status: "authenticated" }),
  clearSession: () =>
    set({ accessToken: null, user: null, status: "anonymous" }),
}));

/**
 * Non-reactive accessor for the current token — used by the client `apiFetch`
 * wrapper outside of React render (architecture.md §5.2).
 */
export function getAccessToken(): string | null {
  return useAuthStore.getState().accessToken;
}
