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
- Claims: `sub` (user_id), `exp`, `iat`, `jti` (unique token ID; denylisted on logout — see H-01 below), `sv` (session-version epoch; tokens below the user's live epoch are rejected — see H-02 below)
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
- JWTs are self-contained — auth is verified without a DB read on the happy path (performance)
- Tradeoff: a self-contained JWT is valid until its `exp` even after logout. Short expiry (15 min) + refresh rotation bound the window; **H-01 (below) closes it** with a small `jti` denylist consulted at validation time.

---

## H-01: Access-token `jti` denylist (logout revocation)

**Status:** Implemented (2026-06-01). Tracks pentest finding PT-01 (reclassified HIGH→LOW; revisit 2026-08-31).

Logout previously revoked only the opaque refresh token, leaving the access JWT replayable until its `exp` (≤15 min). H-01 denylists the access token's `jti` for its remaining lifetime so a stolen or post-logout token cannot be replayed.

- **Storage:** `revoked_access_token` table (`jti` unique-indexed, `user_id` FK CASCADE, `expires_at` = token `exp`, `created_at`). Migration `b1f2c3d4e5a6`.
- **On logout:** the bearer's `jti` is recorded with `expires_at = exp`; an `auth.access_revoked` audit event is written. This fires even on an **access-only logout** (no refresh cookie present).
- **At validation:** `get_current_user` / `optional_current_user` reject a token whose `jti` is denylisted → `401`. The check filters on `expires_at > now`, so correctness never depends on pruning having run.
- **Bounded growth:** `add` is idempotent (double-logout safe) and opportunistically prunes rows past `expires_at`, so the table stays bounded by the 15-min access TTL rather than growing per logout.
- **Orthogonal to formal verification:** H-01 is additive to the CP-7 refresh lifecycle the TLA+ Gate-B trace models — no `trace_emit` changes.

Out of scope (tracked as **H-02**, below): invalidating *all prior* access tokens for a user on re-login / password change.

---

## H-02: Session-version epoch (mass access-token invalidation)

**Status:** Implemented (2026-06-01). Builds on H-01; tracks pentest finding PT-02 (revisit 2026-08-31).

H-01 kills a single token on its own logout. H-02 invalidates **every** prior access token for a user at once when their session epoch changes — needed so a stolen bare access token dies the moment the legitimate owner re-authenticates or rotates their password, without waiting on the per-token `exp`.

- **Mechanism:** a monotonic per-user counter `user.session_version` (default `1`, `server_default '1'`). Migration `c2d3e4f5a6b7`.
- **Stamped on the token:** every access token carries the issuing epoch as the `sv` claim (`create_access_token`); refresh re-issues at the *current* epoch.
- **Bumped on:** (a) **every successful login** — so a fresh login retires tokens from earlier logins; (b) **password change** (`POST /me/password`), which *also* revokes the refresh-token family, making it a hard kill across all devices.
- **At validation:** `get_current_user` / `optional_current_user` reject a token whose `sv` is **below** the user's live `session_version` → `401` (`_reject_if_stale_session`).
- **Fall-through (no mass-401 on deploy):** the check is **skipped** when the `sv` claim is absent (legacy pre-H-02 tokens) or the subject no longer exists — mirroring H-01's no-`jti` fall-through. Legit devices recover transparently via their refresh cookie, which re-issues at the new epoch.
- **Cost:** one extra single-column read (`session_version`) per authenticated request; one counter increment per login / password change. No new per-token rows (contrast H-01's denylist).
- **Orthogonal to formal verification:** like H-01, additive to the CP-7 refresh lifecycle — no `trace_emit` changes.

**Why bump on every login (not only on password change)?** A bare stolen access token (no refresh cookie) is the threat H-02 targets; tying invalidation to the very next legitimate login closes the window without any user-visible action. Legitimate concurrent sessions are not harmed because each holds a refresh cookie and silently re-issues at the new epoch.

---

## OWASP Top 10 Mitigations Summary

| OWASP Category | Mitigation |
|----------------|-----------|
| A01 Broken Access Control | Ownership check mọi repository; **RBAC quan hệ guardian↔child, counselor↔student theo school_id (CP-4)**; **Consent Guard cho <16 (CP-1)**; 403 vs 404 policy |
| A02 Cryptographic Failures | bcrypt cost≥12; JWT HS256; HTTPS; **mã hóa trường nhạy cảm — kết quả trắc nghiệm (Field Crypto, `FIELD_ENCRYPTION_KEY`)**; không PII trong log |
| A03 Injection | Pydantic validation (no raw string interpolation); SQLAlchemy ORM (parameterized queries only); CSP headers |
| A04 Insecure Design | Threat model produced; **DPIA + phân loại rủi ro AI (Luật 134/2025)**; **human-in-the-loop & rationale cho gợi ý (CP-5/CP-6)**; security review trước release |
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
- H-01 adds one DB write per logout and one indexed `jti` lookup per authenticated request; the `revoked_access_token` table self-prunes to stay bounded by the 15-min access TTL
- H-02 adds one single-column `session_version` read per authenticated request and one counter bump per login / password change; no per-token rows. A login from a new device retires the user's other bare access tokens, but sessions holding a refresh cookie re-issue transparently at the new epoch
