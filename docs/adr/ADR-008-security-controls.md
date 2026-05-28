# ADR-008: Security Controls

**Status:** Accepted  
**Date:** 2026-05-27  

---

## Decision

Use **JWT (access) + httpOnly cookie (refresh)** for authentication. Full OWASP Top 10 mitigations. See `docs/security/` for complete threat model and auth design.

---

## Token Strategy Rationale

### Access Token: Short-lived JWT in memory

- Stored in Zustand memory (not localStorage — XSS-safe)
- 15-minute expiry minimizes exposure window if intercepted
- Signed with HS256 (HMAC-SHA256) using a 256-bit secret key
- Claims: `sub` (user_id), `exp`, `iat`, `jti` (unique token ID for future blacklisting)
- Sent as `Authorization: Bearer {token}` header (not in URL, not in cookie)

**Why HS256 and not RS256:**
- Single-service architecture — no need for asymmetric signing (RS256 needed when multiple services verify tokens independently)
- HS256 is simpler, faster, and equally secure when the secret is properly protected

### Refresh Token: Long-lived, httpOnly cookie

- `HttpOnly`: JavaScript cannot read it — immune to XSS token theft
- `Secure`: HTTPS only — immune to network interception
- `SameSite=Strict`: CSRF protection — not sent on cross-origin requests
- Value stored as SHA-256 hash in DB — raw token never in DB (hash-only storage)
- 7-day expiry; rotated on every use (rotation prevents replay attacks)
- Revoked on logout and on suspicious double-use detection

### Why not Session Cookies for Everything

- Sessions require server-side session store (Redis/DB lookup on every request)
- JWTs are self-contained — auth is verified without a DB read (performance)
- Acceptable tradeoff: JWT access token cannot be revoked before expiry → short expiry (15min) + refresh token rotation mitigates this

---

## OWASP Top 10 Mitigations Summary

| OWASP Category | Mitigation |
|----------------|-----------|
| A01 Broken Access Control | Ownership check in every repository method; no object ID exposed without user_id verification; 403 vs 404 policy |
| A02 Cryptographic Failures | bcrypt cost≥12; JWT HS256; HTTPS enforced; no PII in logs |
| A03 Injection | Pydantic validation (no raw string interpolation); SQLAlchemy ORM (parameterized queries only); CSP headers |
| A04 Insecure Design | Threat model produced; security review required before v1 release |
| A05 Security Misconfiguration | No DEBUG mode in production; security headers in Nginx; no exposed admin endpoints |
| A06 Vulnerable Components | `trivy` + `pip-audit` + `npm audit` in CI; dependabot alerts enabled |
| A07 Auth Failures | Rate limiting on /auth/*; generic error messages (no email enumeration); bcrypt timing safety |
| A08 Software Integrity | Signed Docker images; locked dependencies (`uv.lock`, `package-lock.json`) |
| A09 Logging Failures | Structured logs on every request; auth events always logged; no PII/tokens in logs |
| A10 SSRF | No user-controlled URLs fetched in v1; validated if added in v2 |

---

## Password Policy

- Minimum 8 characters
- Must contain: uppercase, lowercase, digit
- No maximum length (bcrypt handles long passwords via HMAC pre-hash)
- Common password check: compare against `rockyou-top10000.txt` (lightweight check)
- Not stored in plain text anywhere — bcrypt hash only

---

## Rate Limiting

| Endpoint group | Limit | Window | By |
|---------------|-------|--------|----|
| POST /auth/register | 5 | 60 min | IP |
| POST /auth/login | 20 | 1 min | IP |
| POST /auth/refresh | 60 | 1 min | IP |
| All other /api/v1/* | 200 | 1 min | User ID |

---

## Consequences

- `SECRET_KEY` must be 32+ bytes of random data; managed via Docker secrets in production
- JWT secret rotation requires re-login of all users (acceptable; documented in runbook)
- Double-use of refresh token triggers account security alert (future: email notification)
