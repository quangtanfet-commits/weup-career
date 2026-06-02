# Email verification — frontend slice (N-3, task #100)

> Status: spec / draft 2026-06-02 · Scope: `frontend/features/auth/*`, new route `frontend/app/(auth)/verify-email/*`, `frontend/lib/api/endpoints/auth.ts`, regenerated `frontend/lib/api/schema.ts`, `frontend/messages/vi.json`, Storybook stories, `frontend/tests/e2e/*`
> Backend (merged, PR #71): [docs/security/email-verification-2026-06.md](../security/email-verification-2026-06.md) — authoritative behavioural contract
> Companion test infra (this slice): one additive backend mailer adapter (`FileMailer`, non-prod only) to let E2E obtain the raw token deterministically — see §7

This is the **frontend half** of N-3. The backend slice is already on `main`: `register`
now returns **`202`** with a generic body (no session, no `UserOut`), `verify-email`
and `resend-verification` exist, and `login` returns **`403 EMAIL_NOT_VERIFIED`**
when the password is correct but `email_verified_at IS NULL`. The frontend currently
**auto-logs-in after register** — that is broken against the new contract and is the
core of what this slice fixes.

## 1. Why — the current FE flow contradicts the backend

`frontend/features/auth/RegisterForm.tsx` today does `register → login → setSession →
redirect`. Against the N-3 backend:

- `register` returns `202` (no `access_token`, no `user`), so the typed `register()`
  client (declared `Promise<UserOut>`) and the subsequent `login()` are both wrong.
- Even if we kept the chained `login()`, it now returns **`403 EMAIL_NOT_VERIFIED`**
  for the just-created account → the user would see a generic error on a successful
  registration.

So the FE must: stop auto-logging-in, show a "check your email" screen, add a
`/verify-email` page that POSTs the token, add a resend affordance, and teach the
**login** form to handle `403 EMAIL_NOT_VERIFIED` and to do the consent routing that
RegisterForm used to do.

## 2. Behavioural contract (FE ↔ BE), per backend §2.1

| Surface | FE behaviour (N-3) |
|---|---|
| `POST /auth/register` → `202` `AcceptedResponse` | No session. Switch RegisterForm into a **"check your email"** notice. Same UX for new / duplicate / under-16 (no oracle — backend already constant). |
| `POST /auth/verify-email` `{token}` → `204` | `/verify-email` page auto-POSTs the `?token=` on mount → success state with a link to **/login**. |
| `verify-email` error (bad / expired / consumed) → generic `401 INVALID_TOKEN` (`422` if token empty) | Generic **invalid-or-expired** state with a **resend** affordance. Never distinguishes "wrong" vs "expired" vs "used" (matches backend non-enumeration). |
| `POST /auth/resend-verification` `{email}` → always `202` | Resend button → always show the same generic "if valid, we re-sent it" notice. Never reveals existence/verified state. |
| `POST /auth/login` → `403 EMAIL_NOT_VERIFIED` (only after correct password) | LoginForm shows a **distinct** "email not verified" message + a **resend** link (prefilled with the entered email). Wrong password still → generic `401` message (unchanged). |
| `POST /auth/login` → `200` for an under-16 verified-but-`PENDING_GUARDIAN_CONSENT` account | Login **succeeds** (email-verified gate passes) and returns a session; LoginForm routes to **/consent** based on `user.account_status` (this routing **moves from** RegisterForm **to** LoginForm). |

Invariants the FE must not break:

- **No enumeration via the UI.** Register, resend, and verify-error states are
  identical regardless of whether the email exists / is verified. No "email already
  registered" / "email not found" copy anywhere.
- **No session before verify.** RegisterForm must not call `setSessionFromToken` /
  `login()` after register.

## 3. UX state machine

### 3.1 Register

```
[form] --submit--> register() --202--> [check-email notice]
                              \--ApiError(non-422)--> inline generic error, stay on form
                              \--422--> RHF field errors (client Zod already guards most)
```

The "check-email notice" shows the **submitted email** ("Chúng tôi đã gửi liên kết xác
minh tới <email>") and a **resend** button (calls `resendVerification(email)` → always
the generic re-sent notice). The guardian notice (under-16) is shown **before** submit
as today (client-side `requiresGuardian(dob)`); the consent *routing* now happens after
login, not here.

### 3.2 Verify (`/verify-email?token=…`)

```
mount: read ?token=
  no token       --> [invalid] state (+ resend affordance via /login)
  token present  --> verifyEmail(token)
       204       --> [success] ("Email đã xác minh" + link to /login)
       401/4xx   --> [invalid-or-expired] (+ resend affordance)
```

States: `verifying` (spinner/`aria-busy`), `success`, `invalid`. The page is a **client
component** (`"use client"`) — it must not be statically prerendered with a token, and
it performs a side-effecting POST, so it runs entirely in the browser. Route is
`app/(auth)/verify-email/page.tsx` (server chrome) wrapping a client
`VerifyEmailClient` that owns the state machine, mirroring how `register/page.tsx`
wraps `RegisterForm`.

### 3.3 Login

```
[form] --submit--> login()
   200 --> setSessionFromToken --> route by account_status:
              pending_guardian_consent --> /consent
              else                     --> redirectTo (default /dashboard)
   403 EMAIL_NOT_VERIFIED --> [not-verified] message + resend link (prefilled email)
   401 (wrong pw / other) --> generic "Email hoặc mật khẩu không đúng"
```

## 4. File-level changes (concrete)

### 4.1 `frontend/lib/api/endpoints/auth.ts`

- `register(payload): Promise<AcceptedResponse>` (was `Promise<UserOut>`); endpoint
  unchanged, return type/JSDoc corrected to "202, no session".
- **new** `verifyEmail(token: string): Promise<void>` → `POST /auth/verify-email`,
  body `{ token }`, 204.
- **new** `resendVerification(email: string): Promise<void>` →
  `POST /auth/resend-verification`, body `{ email }`, 202.
- Add type aliases from the regenerated schema: `AcceptedResponse`,
  `VerifyEmailRequest`, `ResendVerificationRequest`.

### 4.2 `frontend/lib/api/schema.ts` (regenerated, NFR-20)

Regenerate from the live backend OpenAPI so the new request/response components exist
at compile time. Command (backend running on :8000):

```
cd frontend && npm run gen:api   # or the project's existing openapi-typescript script
```

Confirm the generated `components["schemas"]` gains `AcceptedResponse`,
`VerifyEmailRequest`, `ResendVerificationRequest`, and that `RegisterRequest` /
`LoginRequest` are unchanged. (Verify the exact npm script name in `package.json`; if
absent, document the `npx openapi-typescript http://localhost:8000/openapi.json -o
lib/api/schema.ts` invocation in the runbook.)

### 4.3 `frontend/features/auth/RegisterForm.tsx`

- Drop the `login()` + `setSessionFromToken` + `router.replace` chain.
- On `202`: set local `submitted` state to the entered email → render the
  **CheckEmailNotice** (new small component or inline section) instead of the form.
- Keep client Zod validation + guardian notice. Remove `useAuthStore` / `login` /
  `useRouter` imports if no longer used.

### 4.4 new `frontend/features/auth/CheckEmailNotice.tsx`

Presentational: shows the email, a resend button (wires `resendVerification`), and a
"đã gửi" confirmation. Pure props (`email`, `onResend`, `resendState`) so it is
Storybook-able without network.

### 4.5 new `frontend/app/(auth)/verify-email/page.tsx` + `frontend/features/auth/VerifyEmailClient.tsx`

Server page = card chrome + `metadata.title`. Client component owns the
`verifying|success|invalid` state machine from §3.2 and the resend affordance on
`invalid`.

### 4.6 `frontend/features/auth/LoginForm.tsx`

- Add `account_status` routing (moved from RegisterForm): `pending_guardian_consent →
  /consent`, else `redirectTo`.
- Catch `ApiError` with `code === "EMAIL_NOT_VERIFIED"` (status 403) → distinct
  not-verified message + a resend link/button prefilled with the entered email. All
  other errors keep the generic message.

### 4.7 `frontend/messages/vi.json` (`auth` block — new keys)

```
checkEmailTitle:    "Kiểm tra hộp thư của bạn"
checkEmailBody:     "Chúng tôi đã gửi liên kết xác minh tới {email}. Mở email và nhấp vào liên kết để kích hoạt tài khoản."
resend:             "Gửi lại email xác minh"
resendDone:         "Nếu thông tin hợp lệ, chúng tôi đã gửi lại email xác minh."
verifyTitle:        "Xác minh email"
verifying:          "Đang xác minh…"
verifySuccessTitle: "Email đã được xác minh"
verifySuccessBody:  "Tài khoản của bạn đã sẵn sàng. Vui lòng đăng nhập."
verifyInvalidTitle: "Liên kết không hợp lệ hoặc đã hết hạn"
verifyInvalidBody:  "Liên kết xác minh không còn hiệu lực. Hãy yêu cầu gửi lại một liên kết mới."
goLoginCta:         "Đến trang đăng nhập"
emailNotVerified:   "Tài khoản chưa được xác minh email. Vui lòng kiểm tra hộp thư hoặc gửi lại liên kết."
```

(Vietnamese user-facing copy; technical identifiers stay English. Final wording can be
tightened during review.)

## 5. Storybook (full-stack profile)

New stories, each covering all visible states, pinned by Chromatic:

- `CheckEmailNotice.stories.tsx` — `Default`, `Resending`, `ResendDone`.
- `VerifyEmail.stories.tsx` — `Verifying`, `Success`, `Invalid` (render the client
  component's view layer with injected state, or split a presentational
  `VerifyEmailView` so stories need no network).
- `LoginForm` not-verified error state (if LoginForm is story-friendly; otherwise a
  small `AuthError` presentational story).

Do **not** blanket-accept Chromatic baselines — review each new snapshot.

## 6. Accessibility (axe-core)

- Verify page: `aria-busy` during `verifying`; result announced via `role="status"`
  (success) / `role="alert"` (invalid).
- Resend button: disabled + `aria-disabled` while in-flight; success notice in a live
  region.
- All new copy through `next-intl`; labels associated via the existing `FormField`.

## 7. Playwright E2E — strategy + blast radius

### 7.1 The token problem

Post-N-3 a usable session requires a **verified** account, and verification needs the
**raw token** which by design only leaves the system via the email link. The native
harness (`scripts/run-validation-native.sh`) runs Playwright against the **already
running** backend on `:8000` — it does not boot its own backend and cannot use the
pytest `CapturingMailer` (different process). So we need a prod-safe, cross-process way
to read the raw token.

### 7.2 Recommended: `FileMailer` outbox (additive, non-prod only)

Add a third adapter in `backend/app/core/mailer.py`:

```python
class FileMailer:
    """Test/e2e adapter — appends {to, verify_url, ts} as NDJSON to an outbox file
    so an out-of-process harness can read the raw token. Never selected in prod."""
    def __init__(self, path: str) -> None: ...
    async def send_verification_email(self, *, to, verify_url) -> None: ...  # append line
```

Selection in `app/api/deps.py::mailer`: when `not settings.is_production` **and**
`settings.mailer_outbox_path` is set → `FileMailer(path)`; else `ConsoleMailer`;
production still `SmtpMailer` (fail-fast). New optional setting
`mailer_outbox_path: str | None = None` (env `WEUP_MAILER_OUTBOX`).

Runbook change: the `:8000` backend used for E2E is started with
`WEUP_MAILER_OUTBOX=/tmp/weup-outbox.ndjson` (non-prod env, already the case). Document
this in the harness header so a fresh run wires it.

> This is the only backend change in this slice and it is **test infrastructure** —
> prod behaviour (SmtpMailer fail-fast) is untouched, no new HTTP surface, the outbox
> file is local-only. Alternative rejected: a test-only `GET last-verification`
> endpoint — adds an auth-adjacent route even if env-gated; higher risk than a local
> file.

### 7.3 Fixture rework — `frontend/tests/e2e/fixtures/auth.ts`

Keep the public helpers' **signatures and end states** so dependent specs
(counselor / wellbeing / admin-editor / recommendations) keep working:

- new `readVerifyToken(email): string` — read newest NDJSON line in
  `WEUP_MAILER_OUTBOX` matching `to === email`, parse `?token=` from `verify_url`.
- `registerAdult(page, email?)`: fill+submit register → assert **check-email notice**
  → `readVerifyToken` → `page.goto('/verify-email?token=…')` → assert success → then
  `loginAs` → assert `/dashboard`. Returns creds (unchanged shape).
- `registerChild(...)`: same, but after login asserts `/consent` (consent routing now
  on login). 
- New explicit assertions where the value is UI-observable: check-email notice after
  register; verify success page; verify with a bogus token → invalid state; resend
  button → generic notice; login-before-verify → `403` not-verified message.

### 7.4 `frontend/tests/e2e/auth-lifecycle.spec.ts`

- Existing "adult registers and lands on dashboard" / "under-16 → consent" tests now
  pass **through** the verify step (fixtures handle it). Update the stale comments that
  claim "auto-logged-in after register" / "register→login two round-trips".
- The H-04 indistinguishability test: re-registering an existing email now lands on
  the **check-email notice** (same as a fresh email), not the dashboard — update the
  assertion accordingly; the no-oracle property is preserved (identical UX).
- **New** tests: verify-success happy path; verify invalid-token state; resend generic
  notice; login-before-verify 403 message.

Scope note stays honest: token hashing / TTL / single-use / resend-invalidation /
timing are **backend pytest** concerns (already merged). E2E covers only what the user
sees.

## 8. Gates before "done" (full-stack profile)

- `npm run lint` **and** `npm run format:check` (separate CI gate — run prettier).
- `npx tsc --noEmit` (schema regen must type-check end to end).
- Storybook build green; new stories present.
- Playwright (Chromium/Firefox/WebKit) green via the native harness.
- axe-core: no new violations on register/verify/login.
- No enumeration copy introduced; no session created before verify.

## 9. Out of scope

- Real SMTP send (backend §8 — `SmtpMailer` stays a fail-fast seam).
- Cleanup job for expired unverified accounts (future backlog item).
- Any change to the guardian-consent flow itself (only the *routing trigger* moves
  from register to login).
