"use client";

import { create } from "zustand";

import { rolesFromToken } from "@/lib/auth/claims";

/**
 * Authenticated user as surfaced by `/auth/me` / login payload
 * (architecture.md §5.3). The backend `UserOut` body does not include `roles`
 * (roles live in the access-token claims — see `lib/auth/claims.ts`), so the
 * store derives `roles` when a session is created from a token. Kept minimal in
 * F1; later slices widen it as feature pages need more claims.
 */
export interface SessionUser {
  readonly id: string;
  readonly email: string;
  readonly roles: readonly string[];
  readonly age_band?: string;
  readonly account_status?: string;
  readonly user_type?: string;
  readonly school_level?: string;
}

/** Shape of the backend `UserOut` fields the session needs (architecture §6.2). */
export interface BackendUser {
  readonly id: string;
  readonly email: string;
  readonly age_band?: string;
  readonly account_status?: string;
  readonly user_type?: string;
  readonly school_level?: string;
}

/**
 * `loading` is the pre-bootstrap state used while the app attempts a silent
 * session restore via `POST /auth/refresh` on startup (architecture.md §5.1).
 * Guards must treat `loading` as "not yet known" and avoid redirecting until it
 * resolves to `authenticated` or `anonymous`.
 */
export type SessionStatus = "loading" | "anonymous" | "authenticated";

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
  /** Set a session from a pre-built `SessionUser` (tests / explicit callers). */
  setSession: (token: string, user: SessionUser) => void;
  /**
   * Set a session from a backend token-response (`access_token` + `UserOut`).
   * Derives `roles` from the token claims. This is the path login/refresh use.
   */
  setSessionFromToken: (token: string, user: BackendUser) => void;
  clearSession: () => void;
  /** Mark bootstrap as resolved-anonymous (refresh failed / no cookie). */
  finishLoading: () => void;
}

/** Map a backend `UserOut` + access token to the in-memory `SessionUser`. */
export function toSessionUser(token: string, user: BackendUser): SessionUser {
  return {
    id: user.id,
    email: user.email,
    roles: rolesFromToken(token, user.user_type),
    age_band: user.age_band,
    account_status: user.account_status,
    user_type: user.user_type,
    school_level: user.school_level,
  };
}

export const useAuthStore = create<AuthState>((set) => ({
  // App starts in `loading` so the startup refresh can run before guards fire.
  accessToken: null,
  user: null,
  status: "loading",
  setSession: (accessToken, user) =>
    set({ accessToken, user, status: "authenticated" }),
  setSessionFromToken: (accessToken, user) =>
    set({
      accessToken,
      user: toSessionUser(accessToken, user),
      status: "authenticated",
    }),
  clearSession: () =>
    set({ accessToken: null, user: null, status: "anonymous" }),
  finishLoading: () =>
    set((s) => (s.status === "loading" ? { ...s, status: "anonymous" } : s)),
}));

/**
 * Non-reactive accessor for the current token — used by the client `apiFetch`
 * wrapper outside of React render (architecture.md §5.2).
 */
export function getAccessToken(): string | null {
  return useAuthStore.getState().accessToken;
}
