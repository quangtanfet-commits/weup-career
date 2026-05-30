"use client";

import { API_BASE_PATH, publicApiBaseUrl } from "./config";
import { ApiError, toApiError } from "./errors";
import { getAccessToken } from "@/lib/auth/store";

/**
 * Browser-side typed fetch for authenticated/sensitive calls
 * (architecture.md §5.2). It injects the in-memory bearer token from the
 * Zustand auth store, sends cookies for the `/auth/*` refresh flow, and on a
 * 401 transparently refreshes the session once and retries (CP-7).
 */
export interface ClientFetchOptions extends Omit<RequestInit, "body"> {
  readonly body?: unknown;
  readonly query?: Record<string, string | undefined>;
  /**
   * Skip the refresh-on-401 interceptor for this call. Set on `/auth/refresh`
   * itself (a 401 there means "not logged in", not "token expired") so the
   * interceptor never recurses into an infinite refresh loop.
   */
  readonly skipAuthRefresh?: boolean;
}

function buildUrl(path: string, query?: ClientFetchOptions["query"]): string {
  const base = `${publicApiBaseUrl()}${API_BASE_PATH}${path}`;
  if (!query) return base;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== "") params.set(key, value);
  }
  const qs = params.toString();
  return qs ? `${base}?${qs}` : base;
}

function buildRequestInit(
  body: unknown,
  rest: Omit<RequestInit, "body">,
  token: string | null,
  headers?: HeadersInit,
): RequestInit {
  const mergedHeaders = new Headers(headers);
  mergedHeaders.set("Accept", "application/json");
  if (body !== undefined) {
    mergedHeaders.set("Content-Type", "application/json");
  }
  if (token) {
    mergedHeaders.set("Authorization", `Bearer ${token}`);
  }
  return {
    ...rest,
    headers: mergedHeaders,
    // The refresh cookie is httpOnly and scoped to /api/v1/auth; include it.
    credentials: "include",
    body: body === undefined ? undefined : JSON.stringify(body),
  };
}

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw await toApiError(response);
  }
  // 204 No Content has an empty body.
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function apiFetch<T>(
  path: string,
  options: ClientFetchOptions = {},
): Promise<T> {
  const { body, query, headers, skipAuthRefresh, ...rest } = options;
  const url = buildUrl(path, query);

  const response = await fetch(
    url,
    buildRequestInit(body, rest, getAccessToken(), headers),
  );

  // Refresh-on-401 (architecture.md §5.2, CP-7): on a 401, attempt a single
  // shared refresh, then replay the original request once with the new token.
  // `skipAuthRefresh` short-circuits this for `/auth/refresh` itself.
  if (response.status === 401 && !skipAuthRefresh) {
    // Lazy import breaks the client ↔ session-restore module cycle.
    const { restoreSession, notifyAuthLost } =
      await import("@/lib/auth/session-restore");
    const newToken = await restoreSession();
    if (newToken === null) {
      notifyAuthLost();
      throw await toApiError(response);
    }
    const retry = await fetch(
      url,
      buildRequestInit(body, rest, newToken, headers),
    );
    if (retry.status === 401) {
      // Still unauthorised after a fresh token → give up (no infinite retry).
      notifyAuthLost();
      throw new ApiError(401, "Phiên đăng nhập đã hết hạn", "UNAUTHORIZED");
    }
    return parse<T>(retry);
  }

  return parse<T>(response);
}
