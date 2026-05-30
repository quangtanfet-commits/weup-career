/**
 * Backend URL resolution (architecture.md §5.4).
 *
 * - `BACKEND_INTERNAL_URL` is a **server-only** variable used by anonymous RSC
 *   fetches (public career/content reads). It must never be exposed to the
 *   client bundle, so it is read without the `NEXT_PUBLIC_` prefix.
 * - `NEXT_PUBLIC_API_BASE_URL` is the browser-facing base for authed client
 *   calls that carry the in-memory bearer token.
 *
 * Both default to the conventional dev host so a bare `next dev` works.
 */
export const API_BASE_PATH = "/api/v1";

/** Server-only base for anonymous RSC reads. Not shipped to the client. */
export function backendInternalUrl(): string {
  const raw = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";
  return raw.replace(/\/+$/, "");
}

/** Browser-facing base for authed client calls. */
export function publicApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  return raw.replace(/\/+$/, "");
}
