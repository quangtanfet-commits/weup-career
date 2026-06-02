# Native E2E — harness-owned backend + FileMailer outbox (N-3)

**Status:** accepted · **Date:** 2026-06-02 · **Scope:** `scripts/run-validation-native.sh` e2e step only

## Problem

Post-N-3 (`docs/frontend/email-verification-2026-06.md`) registration no longer
opens a session. The Playwright fixtures (`frontend/tests/e2e/fixtures/auth.ts`)
must recover the mailed verification token to complete `register → verify →
login`. They read it from the backend's **FileMailer outbox** — an NDJSON file
the backend appends to whenever `/auth/register` or `/auth/resend-verification`
"sends" a verification email.

Two preconditions were unmet by the native harness:

1. The backend must run with `WEUP_MAILER_OUTBOX` set so `app/api/deps.py`
   selects `FileMailer` (non-prod) instead of `ConsoleMailer`, and writes the
   outbox.
2. A WeUp backend must be listening on `:8000` at all. The harness assumed one
   was already started by hand; in CI / a clean box there is none, so the e2e
   gate could not run.

The Playwright process must also read the **same** outbox path the backend
writes — the fixtures default to `/tmp/weup-outbox.ndjson` but honor
`WEUP_MAILER_OUTBOX` when set.

## Decision

The harness **owns an ephemeral backend** for the e2e step: it boots one on
`:8000` with a run-scoped `WEUP_MAILER_OUTBOX`, waits for readiness, runs
Playwright with the **same** env var, then tears the backend down. This makes
the gate self-contained and reproducible (local + CI) without depending on a
hand-started backend.

### Details

- **Outbox path:** `report/<run-id>/e2e/outbox.ndjson` (absolute). `report/` is
  gitignored, and a run-scoped file avoids stale tokens leaking across runs
  (the fixtures scan newest-first, so a shared `/tmp` file could surface a token
  from a previous run).
- **Hermetic DB copy + upgrade:** the seeded `backend/data/app.db` was one
  migration behind head (it lacked N-3's `email_verification_tokens` table and
  `email_verified_at` column), so register's token INSERT 500s against it. The
  harness copies the seed to a run-scoped `report/<run-id>/e2e/app.db`, points
  `DATABASE_URL` at the copy, and runs `uv run alembic upgrade head` on it.
  `migrations/env.py` reads `get_settings().database_url`, so the one override
  redirects **both** alembic and the backend at the copy — the developer's
  `backend/data/app.db` is never mutated and its seed reference data is
  preserved. If no seed exists the copy is skipped and `alembic upgrade head`
  creates the DB fresh. A failed migration is recorded as an `e2e-db` failure.
- **Backend command:** `uv run uvicorn app.main:get_app --factory --port 8000`,
  launched under `setsid` (see Teardown), cwd `backend/`. The ASGI entrypoint is
  the **factory** `get_app()` — `app.main:app` does not exist. Default
  `environment=development` ⇒ non-prod ⇒ `FileMailer` chosen
  when the outbox env is set. No `--reload` (clean single process).
- **Rate limiting off (test-env config):** the backend is booted with
  `RATE_LIMIT_ENABLED=false` (scoped to the setsid process). The 3-browser
  Playwright suite registers far more accounts than the production register
  bucket allows (`rate_limit_register_max=5` / 3600s), so a live limiter 429s the
  suite. Rate limiting is a product invariant owned by **backend pytest**
  (`test_rate_limit*`), not a UI-observable behaviour — disabling it for the e2e
  backend is a harness config, not a weakened gate. The port-guard reuse branch
  (a hand-started backend) is untouched.
- **Readiness:** poll `http://localhost:8000/api/v1/health` (up to 60s) before
  building/serving the frontend. A backend that never becomes ready is recorded
  as an `e2e-backend` failure (fault-tolerant, like every other suite — the HTML
  report is still produced).
- **Teardown:** `uv run uvicorn` forks a child uvicorn (`.venv/bin/python`) that
  actually holds `:8000`; killing only the wrapper PID orphans the listener. The
  harness launches the backend under `setsid` so the wrapper is a process-group
  leader, captures its PID as the PGID, and tears the whole tree down with
  `kill -- -"$PGID"` — both next to the `next start` kill and via an `EXIT` trap,
  so an aborted run leaves no stray uvicorn on `:8000`.
- **Port guard:** if `:8000` is already listening, the harness does **not** boot
  its own (it would fail to bind) — it reuses the existing backend and `warn`s
  that the outbox env may not be set there. This keeps a developer's
  hand-started backend working while making the unattended path self-contained.
- **Both processes share the env:** `WEUP_MAILER_OUTBOX` is exported before the
  backend boot and passed to the Playwright invocation, so writer and reader
  agree on the path.

## Non-goals / unchanged

- The frontend build/serve flow (`next build` same-origin `/api` → `next start
  -p 3100`, `E2E_PROXY_API=1` rewrite to `:8000`) is unchanged.
- Backend API/DB-level invariants (token hashing, single-use, expiry, rotation)
  remain owned by backend pytest — the e2e layer only exercises UI-observable
  behaviour.
- No CI workflow file is modified by this change; only the native harness
  script. (CI wiring, if desired, is a separate doc-first change.)

## Verification

`PW_PROJECT="" scripts/run-validation-native.sh` runs Playwright across all
three browsers + axe-core green, with the outbox written by the harness-owned
backend and consumed by the fixtures.
