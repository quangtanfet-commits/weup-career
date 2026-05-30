/**
 * Best-effort decode of the in-memory access-token JWT payload
 * (architecture.md §5.3, §5.1).
 *
 * The backend `UserOut` body returned by `/auth/register`·`/login`·`/me` does
 * **not** carry `roles` — roles live in the signed access-token claims
 * (`backend/app/core/security.py`: `roles`, `user_type`). The FE holds that
 * token in memory, so it can read the (already-trusted) payload to surface a
 * navigation hint. This is a HINT only: the backend re-derives authority per
 * request and is the final enforcement layer (architecture.md §5.3 "nguồn sự
 * thật"). We never verify the signature client-side and never treat these
 * claims as an authorisation decision.
 *
 * Note: guardian/counselor/school_admin are DB-relational (school membership),
 * not access-token claims, so they do not appear here in F1.
 */

export interface AccessTokenClaims {
  readonly sub?: string;
  readonly email?: string;
  readonly user_type?: string;
  readonly account_status?: string;
  readonly age_band?: string;
  readonly roles?: readonly string[];
}

function base64UrlDecode(segment: string): string | null {
  try {
    const padded = segment.replace(/-/g, "+").replace(/_/g, "/");
    // atob exists in the browser and in jsdom (test env).
    const binary = atob(padded);
    // Decode UTF-8 bytes so non-ASCII claim values survive.
    const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
    return new TextDecoder().decode(bytes);
  } catch {
    return null;
  }
}

/**
 * Parse the JWT payload without verifying the signature. Returns an empty
 * object for any malformed token — callers must tolerate missing claims.
 */
export function decodeAccessTokenClaims(token: string): AccessTokenClaims {
  const parts = token.split(".");
  if (parts.length < 2 || !parts[1]) return {};
  const json = base64UrlDecode(parts[1]);
  if (json === null) return {};
  try {
    const parsed: unknown = JSON.parse(json);
    if (!parsed || typeof parsed !== "object") return {};
    return parsed as AccessTokenClaims;
  } catch {
    return {};
  }
}

/**
 * Roles the client can rely on for navigation hints. Prefers the signed
 * `roles` claim; falls back to `[user_type]` so a student/working user always
 * has at least their base role even if the claim shape changes.
 */
export function rolesFromToken(
  token: string | null | undefined,
  fallbackUserType?: string,
): readonly string[] {
  if (token) {
    const claims = decodeAccessTokenClaims(token);
    if (Array.isArray(claims.roles) && claims.roles.length > 0) {
      return claims.roles.filter((r): r is string => typeof r === "string");
    }
    if (typeof claims.user_type === "string") return [claims.user_type];
  }
  return fallbackUserType ? [fallbackUserType] : [];
}
