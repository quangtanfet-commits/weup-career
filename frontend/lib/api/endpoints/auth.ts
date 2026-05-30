"use client";

import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

/**
 * Authenticated/auth-flow endpoints (architecture.md §6.2, group `auth`).
 * Request/response shapes come straight from the generated OpenAPI schema so
 * the FE↔BE contract is compile-time checked (NFR-20). These run on the client
 * with the in-memory bearer token; `/login`/`/refresh` additionally rely on the
 * httpOnly refresh cookie (`credentials: "include"` in `apiFetch`).
 */
export type RegisterRequest = components["schemas"]["RegisterRequest"];
export type LoginRequest = components["schemas"]["LoginRequest"];
export type TokenResponse = components["schemas"]["TokenResponse"];
export type UserOut = components["schemas"]["UserOut"];

/** POST /auth/register — 201 with the created `UserOut` (no token yet). */
export async function register(payload: RegisterRequest): Promise<UserOut> {
  return apiFetch<UserOut>("/auth/register", { method: "POST", body: payload });
}

/** POST /auth/login — sets the refresh cookie and returns access token + user. */
export async function login(payload: LoginRequest): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: payload,
  });
}

/**
 * POST /auth/refresh — rotates the refresh cookie and returns a new access token
 * + user (architecture.md §5.1/§5.2, CP-7). Used by the startup session restore
 * and by the refresh-on-401 interceptor. `skipAuthRefresh` is set so a 401 here
 * does NOT recurse back into the interceptor (it just means "not logged in").
 */
export async function refresh(): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/refresh", {
    method: "POST",
    skipAuthRefresh: true,
  });
}

/** GET /auth/me — re-reads the current user (session bootstrap / refresh). */
export async function getMe(): Promise<UserOut> {
  return apiFetch<UserOut>("/auth/me");
}

/** POST /auth/logout — server-side refresh-token revoke (204). */
export async function logout(): Promise<void> {
  await apiFetch<void>("/auth/logout", { method: "POST" });
}
