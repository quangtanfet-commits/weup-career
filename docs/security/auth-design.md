# Authentication & Authorization Design

**Version:** 1.0.0 | **Date:** 2026-05-27

---

## Authentication Architecture

### Token Lifecycle Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Token Lifecycle                         │
│                                                                 │
│  Register/Login                                                 │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────┐     ┌──────────────────────────────┐      │
│  │  access_token   │     │      refresh_token           │      │
│  │  (JWT, 15 min)  │     │  (random UUID, 7 days)       │      │
│  │  in: memory     │     │  in: httpOnly cookie         │      │
│  │  sent: Bearer   │     │  sent: automatically by      │      │
│  │  header         │     │  browser on /auth/refresh    │      │
│  └─────────────────┘     └──────────────────────────────┘      │
│           │                         │                           │
│           │ expires in 15min        │ refresh auto-triggered    │
│           │                         │ 60s before access expiry  │
│           │                         │                           │
│           ▼                         ▼                           │
│       401 response ──────────► Token Rotation                   │
│                              New access_token +                  │
│                              New refresh_token issued            │
│                              Old refresh_token revoked           │
└─────────────────────────────────────────────────────────────────┘
```

---

## JWT Claims Structure

### Access Token

```json
{
  "sub": "usr_01HX...",        // User UUID (subject)
  "email": "user@example.com", // Denormalized for convenience (no DB lookup)
  "iat": 1716800000,           // Issued at
  "exp": 1716800900,           // Expires at (15 min from iat)
  "jti": "tkn_01HX...",       // JWT ID (unique per token; future blacklist support)
  "iss": "todo-api"            // Issuer
}
```

**Note:** `email` is included to avoid a DB lookup on every authenticated request. The JWT is verified via signature — no DB round-trip. If a user changes their email, old JWTs will have stale email until expiry (15 min max — acceptable).

---

## Password Storage

```
User input: "MyPassword123"
     │
     ▼
bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
     │
     ▼
Stored: "$2b$12$..." (60-char hash string)
```

**Verification:**
```python
bcrypt.checkpw(candidate.encode(), stored_hash.encode())
# Returns True/False; timing is constant regardless of match
```

**Why bcrypt (not Argon2id):**
- bcrypt is well-established and universally supported
- Argon2id is the modern best-practice; can be adopted in v2 without breaking existing hashes (migrate on next login)
- passlib handles algorithm negotiation transparently

---

## Refresh Token Rotation

```
Client                              Server
  │                                   │
  │── POST /auth/refresh ────────────►│
  │   Cookie: refresh_token=RT_OLD    │
  │                                   │ 1. Hash RT_OLD → lookup in DB
  │                                   │ 2. Verify: not revoked, not expired
  │                                   │ 3. Create RT_NEW (new UUID)
  │                                   │    and AT_NEW (new JWT)
  │                                   │ 4. In same transaction:
  │                                   │    - INSERT RT_NEW (active)
  │                                   │    - UPDATE RT_OLD SET revoked_at=NOW()
  │◄── 200 {access_token: AT_NEW} ───│
  │    Set-Cookie: refresh_token=RT_NEW│
  │                                   │
```

**Re-use detection:** If RT_OLD is presented again after rotation, it is already revoked. This indicates either:
- A race condition (client sent request twice — benign, second returns 401)
- Session hijacking (attacker has the old token — treat as compromise)

Future enhancement: on refresh token reuse, revoke **all** refresh tokens for that user.

---

## Authorization Model

### Current: Flat RBAC (v1)

All authenticated users have identical permissions over their own resources.

```
Authenticated User can:
  ├── CRUD their own todos
  ├── CRUD their own tags
  ├── Read/update their own profile
  └── Change their own password

Authenticated User CANNOT:
  ├── Access any other user's todos (enforced at repository layer)
  ├── Access any other user's tags
  └── See other users exist at all
```

### Ownership Enforcement (Critical)

Every repository method that reads or modifies a resource includes a `user_id` filter:

```python
# CORRECT — safe
async def get_todo(self, todo_id: UUID, user_id: UUID) -> Todo | None:
    result = await self.session.execute(
        select(TodoModel)
        .where(TodoModel.id == todo_id)
        .where(TodoModel.user_id == user_id)   # ← OWNERSHIP CHECK
        .where(TodoModel.is_deleted == False)
    )
    return result.scalar_one_or_none()

# WRONG — never do this
async def get_todo_unsafe(self, todo_id: UUID) -> Todo | None:
    # No user_id filter — IDOR vulnerability
    ...
```

**Defense in depth:** The service layer also checks ownership, but the repository is the final enforcement layer.

---

## Session Security Configuration

### Nginx Security Headers

```nginx
# Strict Transport Security (HTTPS only)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

# Prevent clickjacking
add_header X-Frame-Options "DENY" always;

# Prevent MIME type sniffing
add_header X-Content-Type-Options "nosniff" always;

# Content Security Policy
add_header Content-Security-Policy "
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data:;
  connect-src 'self';
  font-src 'self';
  object-src 'none';
  frame-ancestors 'none';
" always;

# Referrer Policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Permissions Policy
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
```

---

## Secret Management

### Development
- `SECRET_KEY` in `.env` (gitignored)
- `.env.example` shows required variable names without values

### Production
- Docker secret mounted at `/run/secrets/secret_key`
- Application reads from file path, not env var
- Rotation procedure: update secret file → rolling restart

### Key Generation
```bash
openssl rand -hex 32   # Generates 256-bit key
```

---

## Audit Logging

Every authenticating event produces a log entry with:

```json
{
  "event": "auth.login.success",
  "user_id": "usr_01HX...",
  "ip_address": "1.2.3.4",
  "user_agent": "Mozilla/5.0...",
  "request_id": "req_01HX..."
}
```

Events logged:
- `auth.register.success` / `auth.register.failed`
- `auth.login.success` / `auth.login.failed`
- `auth.logout`
- `auth.token.refreshed`
- `auth.token.refresh_failed`
- `auth.token.reuse_detected` (future: triggers security alert)
- `user.password_changed`
- `user.account_deleted`
