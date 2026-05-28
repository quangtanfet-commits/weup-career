# Threat Model

**Version:** 1.0.0 | **Date:** 2026-05-27  
**Framework:** STRIDE  
**Scope:** Todo Application v1 (Backend API + Frontend SPA + Docker deployment)

---

## System Overview for Threat Modeling

```
[Internet]
    │
    ▼
[Nginx — TLS termination, rate limiting, security headers]
    │
    ├──→ [Static Files — Frontend SPA bundle]
    │
    └──→ [Backend API — FastAPI]
              │
              └──→ [SQLite Database]
```

**Trust Boundaries:**
1. Internet → Nginx (TLS; untrusted input)
2. Nginx → Backend API (internal Docker network; trusted)
3. Backend API → SQLite (same container or mounted volume; trusted)

---

## STRIDE Threat Analysis

### S — Spoofing

| Threat | Asset | Likelihood | Impact | Mitigation |
|--------|-------|-----------|--------|-----------|
| Attacker spoofs a legitimate user's session | Auth tokens | Medium | Critical | JWT signature verification; httpOnly cookie for refresh token; token rotation on use |
| Attacker registers with another user's email | User identity | Low | Medium | Email uniqueness constraint; bcrypt prevents credential stuffing |
| Attacker replays a refresh token | Refresh token | Low | High | Single-use rotation; revocation on logout; SHA-256 hash stored (raw never in DB) |
| Attacker presents a forged JWT | Access token | Low | Critical | HS256 signature verification; server-side secret key validation; exp claim enforced |

**Mitigations implemented:**
- All protected routes require valid, unexpired JWT signature verification
- Refresh token value is hashed before storage — even a DB dump reveals only hashes
- Token rotation: using a refresh token immediately invalidates it and issues a new one

---

### T — Tampering

| Threat | Asset | Likelihood | Impact | Mitigation |
|--------|-------|-----------|--------|-----------|
| Attacker modifies todo data of another user | Todo records | Medium | High | user_id ownership check on every DB query; SQLAlchemy WHERE user_id = current_user.id |
| Attacker tampers with JWT claims (e.g., changes user_id) | JWT payload | Low | Critical | HS256 signature; any modification invalidates signature |
| Attacker modifies request body to inject SQL | DB queries | Low | Critical | SQLAlchemy ORM parameterized queries; Pydantic input validation |
| Attacker tampers with API response in transit | Response data | Low | High | HTTPS enforced (Nginx TLS); HSTS header |

**Mitigations implemented:**
- All API mutations verify the requested resource belongs to `current_user`
- No raw SQL strings; all queries through SQLAlchemy ORM
- HTTPS with TLS 1.2+ minimum; HSTS with max-age=31536000

---

### R — Repudiation

| Threat | Asset | Likelihood | Impact | Mitigation |
|--------|-------|-----------|--------|-----------|
| User denies performing an action (todo delete, etc.) | Audit trail | Low | Medium | Structured logs with user_id and action on every mutating operation |
| Attacker covers tracks by manipulating logs | Log integrity | Very Low | Medium | Logs to stdout (container) → external log shipper; not modifiable by app |

**Mitigations implemented:**
- Every request logged with: timestamp, user_id (post-auth), method, path, status_code, request_id
- Soft deletes preserve records with timestamps (30-day window)
- Logs streamed to stdout; not stored in a file the application can write to

---

### I — Information Disclosure

| Threat | Asset | Likelihood | Impact | Mitigation |
|--------|-------|-----------|--------|-----------|
| Stack traces exposed in API 500 responses | Internal architecture | Low | Low | All exceptions caught; generic "Internal server error" returned; full trace in logs only |
| Tokens logged | Auth tokens | Low | Critical | Tokens never logged; structured logger strips `Authorization` header |
| Email enumeration via login error messages | User email list | Medium | Low | Generic "Invalid email or password" for all auth failures |
| DB file accessible on disk | All user data | Very Low | Critical | DB volume owned by appuser; not bind-mounted in production; Docker secrets for config |
| Error messages leak email existence on register | User email list | Low | Low | Register returns 409 Conflict without specifying what already exists (or use generic message) |
| Sensitive query params in logs | URLs | Low | Medium | Log path but not query string content; filter `password=` patterns |

**Mitigations implemented:**
- `expose_server_errors=False` equivalent: never expose tracebacks to clients
- Log sanitization: `Authorization` header stripped from access logs
- Generic auth error messages across all failure modes

---

### D — Denial of Service

| Threat | Asset | Likelihood | Impact | Mitigation |
|--------|-------|-----------|--------|-----------|
| Brute force login (credential stuffing) | User accounts | High | High | Rate limit: 20 /auth/login req/min per IP; bcrypt slowness inherent defense |
| Auth endpoint flood (unauthenticated) | Server availability | Medium | Medium | Rate limit: 5 /register + 20 /login req/min per IP; Nginx limit_req |
| Large payload upload | Server memory | Low | Low | Nginx `client_max_body_size 1m`; Pydantic max field length validation |
| Long-running DB query | Server availability | Very Low | Medium | SQLite WAL; async IO; query timeouts (SQLAlchemy `connect_args`) |
| Malformed JSON body | Server stability | Low | Low | Pydantic parses and rejects; no crash; 422 response |

**Mitigations implemented:**
- slowapi rate limiter on all endpoints
- Nginx `limit_req_zone` as first line of defense (before Python code runs)
- Max request body: 1MB (configurable)

---

### E — Elevation of Privilege

| Threat | Asset | Likelihood | Impact | Mitigation |
|--------|-------|-----------|--------|-----------|
| User accesses another user's todos via IDOR | Todo ownership | Medium | High | user_id ownership check on EVERY read/write in repository layer; returns 404 (not 403) to avoid confirming existence |
| User escalates to admin (no admin role in v1) | Authorization | Low | N/A | No admin role in v1; all users equal; no privilege escalation surface |
| Attacker uses stolen expired token | Auth tokens | Low | Medium | JWT exp claim enforced; expired tokens rejected regardless of signature validity |
| Attacker runs code via injection in todo title | Process | Very Low | Critical | CSP headers; Pydantic input sanitization; no eval() anywhere; parameterized SQL |

**Mitigations implemented:**
- IDOR protection: `WHERE todo.user_id = current_user.id AND todo.id = ?` on all resource access
- Returns 404 (not 403) when resource doesn't belong to user — avoids confirming existence
- Content Security Policy headers prevent XSS execution even if injected

---

## DREAD Risk Scores

| Threat | D | R | E | A | D | Total | Priority |
|--------|---|---|---|---|---|-------|----------|
| JWT spoofing via key compromise | 10 | 7 | 8 | 8 | 6 | 39 | **Critical** |
| IDOR — user accesses another user's todos | 7 | 8 | 5 | 7 | 8 | 35 | **High** |
| Credential stuffing / brute force | 8 | 7 | 7 | 8 | 6 | 36 | **High** |
| SQL injection | 10 | 4 | 8 | 5 | 4 | 31 | High |
| Refresh token replay | 9 | 4 | 5 | 5 | 5 | 28 | Medium |
| Email enumeration | 3 | 7 | 3 | 8 | 7 | 28 | Medium |
| XSS in todo content | 7 | 5 | 5 | 5 | 4 | 26 | Medium |
| Stack trace disclosure | 3 | 5 | 2 | 7 | 7 | 24 | Low |

*(D=Damage, R=Reproducibility, E=Exploitability, A=Affected users, D=Discoverability, scale 1-10)*

---

## Residual Risks Accepted

| Risk | Reason Accepted |
|------|----------------|
| Single point of failure (single node v1) | Intentional for v1 simplicity; HA in Phase 3 |
| No email-based account recovery | SMTP integration deferred to v2 |
| No 2FA / MFA | Deferred to v2 |
| SQLite single-writer bottleneck | Acceptable at v1 scale; migration path designed |
| No audit log for READ operations | Read-heavy workload; too noisy; writes are audited |
