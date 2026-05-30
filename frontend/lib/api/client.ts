"use client";

import { API_BASE_PATH, publicApiBaseUrl } from "./config";
import { toApiError } from "./errors";
import { getAccessToken } from "@/lib/auth/store";

/**
 * Browser-side typed fetch for authenticated/sensitive calls
 * (architecture.md §5.2). It injects the in-memory bearer token from the
 * Zustand auth store and sends cookies for the `/auth/*` refresh flow.
 *
 * F1 ships the token-injection + error-envelope handling; the single-flight
 * refresh-on-401 interceptor (CP-7) is layered on in the auth slice (F1 auth
 * pages) — this wrapper is the seam it hooks into.
 */
export interface ClientFetchOptions extends Omit<RequestInit, "body"> {
  readonly body?: unknown;
  readonly query?: Record<string, string | undefined>;
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

export async function apiFetch<T>(
  path: string,
  options: ClientFetchOptions = {},
): Promise<T> {
  const { body, query, headers, ...rest } = options;
  const token = getAccessToken();

  const mergedHeaders = new Headers(headers);
  mergedHeaders.set("Accept", "application/json");
  if (body !== undefined) {
    mergedHeaders.set("Content-Type", "application/json");
  }
  if (token) {
    mergedHeaders.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(buildUrl(path, query), {
    ...rest,
    headers: mergedHeaders,
    // The refresh cookie is httpOnly and scoped to /api/v1/auth; include it.
    credentials: "include",
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!response.ok) {
    throw await toApiError(response);
  }
  // 204 No Content has an empty body.
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}
