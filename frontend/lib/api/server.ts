import "server-only";

import { API_BASE_PATH, backendInternalUrl } from "./config";
import { toApiError } from "./errors";

/**
 * Anonymous server-side fetch for **public** reads from React Server Components
 * (architecture.md §5.4). It NEVER attaches an `Authorization` header — the
 * backend (BE-1) makes the career/content GETs anonymous-readable and enforces
 * the published-only invariant server-side. Sensitive/personal data must not be
 * fetched here (it would leak into the RSC cache).
 *
 * `revalidate` enables ISR for public content, which is versioned by
 * `school_level` and updated by content editors (FR-90).
 */
export interface PublicFetchOptions {
  /** Query parameters appended to the path. */
  readonly query?: Record<string, string | undefined>;
  /** ISR revalidation window in seconds. Defaults to 1 hour. */
  readonly revalidate?: number;
}

function buildUrl(path: string, query?: PublicFetchOptions["query"]): string {
  const base = `${backendInternalUrl()}${API_BASE_PATH}${path}`;
  if (!query) return base;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== "") params.set(key, value);
  }
  const qs = params.toString();
  return qs ? `${base}?${qs}` : base;
}

export async function publicFetch<T>(
  path: string,
  options: PublicFetchOptions = {},
): Promise<T> {
  const { query, revalidate = 3600 } = options;
  const response = await fetch(buildUrl(path, query), {
    method: "GET",
    headers: { Accept: "application/json" },
    // Anonymous — no Authorization header. ISR cache for SEO + fast loads.
    next: { revalidate },
  });

  if (!response.ok) {
    throw await toApiError(response);
  }
  return (await response.json()) as T;
}
