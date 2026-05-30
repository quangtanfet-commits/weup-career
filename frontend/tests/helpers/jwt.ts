/**
 * Test helper: build an unsigned-but-well-formed JWT for unit tests. The client
 * only ever DECODES the payload (it never verifies the signature — the backend
 * is the authority, see lib/auth/claims.ts), so a dummy signature is sufficient
 * to exercise claim parsing. UTF-8 is encoded so non-ASCII claim values survive.
 */
function base64Url(input: string): string {
  const bytes = new TextEncoder().encode(input);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function encodeTestToken(payload: Record<string, unknown>): string {
  const header = base64Url(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body = base64Url(JSON.stringify(payload));
  return `${header}.${body}.testsignature`;
}
