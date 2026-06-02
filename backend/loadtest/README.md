# N-1 load test (Gate C, NFR-01) — native Locust harness

Turns NFR-01 from an aspirational SLO into a **measured single-node baseline**.
Full rationale, scope, and the pass/fail gate live in
[`docs/performance/n1-load-test-2026-06.md`](../../docs/performance/n1-load-test-2026-06.md).

| | SLO | At |
|---|---|---|
| read group | p99 < 150 ms | 200 concurrent users |
| write group | p99 < 300 ms | 200 concurrent users |
| error-rate | < 0.1 % | — |

The single-node SQLite numbers are **floor-not-ceiling**: they prove the code
path is not pathologically slow and expose per-endpoint hotspots. The Postgres +
multi-node ceiling is a separate exercise (ADR-002).

## What it does

`locustfile.py`:

- **`test_start`** mints a real **adult** cohort — `register → verify (read the
  FileMailer outbox) → login → submit RIASEC → generate recommendation` — and
  persists it to a JSON file. Adults clear the consent gate without a guardian
  dance yet still drive the sensitive read (field-decrypt + append-only audit,
  CP-3) exactly as in production. **No faked tokens.**
- **`WeUpUser`** runs a read-heavy 85/15 mix:

  | Task | Weight | Endpoint | Group |
  |---|---|---|---|
  | `me_assessment_read` | 35 | `GET /me/assessments/[id]` (decrypt+audit) | read |
  | `careers_browse` | 25 | `GET /careers` + `GET /careers/[id]` | read |
  | `reco_read` | 15 | `GET /recommendations/[id]` | read |
  | `auth_me` | 10 | `GET /auth/me` | read |
  | `riasec_submit` | 10 | `POST /assessments/riasec/submit` (encrypt+audit) | write |
  | `reco_generate` | 5 | `POST /recommendations` | write |

Path-param endpoints are reported under a stable `name=` so percentiles are
per **group**, not per concrete id.

## Run it (the easy way)

```bash
scripts/run-loadtest-native.sh
```

This boots an **ephemeral, hermetic** backend on `:8100` (own DB copy, FileMailer
outbox, rate limiting OFF) so it never touches your `:8000` dev backend, then
runs Locust in two phases:

1. **warm-up + cohort build** — builds the cohort and warms the SQLite page
   cache; stats discarded.
2. **measured baseline** — ramp 0→200 then steady, `--reset-stats` excludes the
   ramp from the percentiles.

Artifacts land under `report/<run-id>/loadtest/`:
`baseline_stats.csv`, `verdict.json`, `cohort.json`, and per-phase `*.log`. The
script prints a per-group verdict and exits non-zero if the gate fails. It does
**not** edit `docs/spec.md` — ticking Gate C is a deliberate manual step after
review.

Tunables (env): `LT_BACKEND_PORT` (8100), `COHORT_SIZE` (50), `RUN_USERS` (200),
`SPAWN_RATE` (4), `RUN_TIME` (6m), `WARMUP_TIME` (90s).

## Run it manually (against an already-running backend)

The backend must have been booted with `WEUP_MAILER_OUTBOX` set (so the cohort
builder can recover verification tokens) and ideally `RATE_LIMIT_ENABLED=false`
(a 200-VU run blows past the register/login buckets).

```bash
export WEUP_MAILER_OUTBOX=/tmp/weup-loadtest-outbox.ndjson
uv run --project backend locust -f backend/loadtest/locustfile.py --headless \
    --host http://localhost:8000 -u 200 -r 4 -t 6m --reset-stats \
    --cohort-size 50 --cohort-file /tmp/weup-cohort.json \
    --csv report/manual/loadtest/baseline --csv-full-history
```

Custom flags: `--cohort-size N` (accounts to mint), `--cohort-file PATH`
(load-or-persist the cohort so a second invocation reuses it).

## Notes

- **Rate limiting** is a product invariant owned by backend pytest
  (`test_rate_limit*`), not the latency subject — the harness disables it so it
  measures latency, not 429s.
- The cohort file is **run-scoped**; delete it (or use a fresh path) to rebuild.
- `report/` is gitignored — artifacts and the minted-account outbox never land
  in the repo.
- **Cohort-builder retries (gevent read-after-write).** The builder chains
  `register → verify → login` back-to-back with zero think-time. Locust
  monkey-patches with gevent, and under that scheduling the SQLite + aiosqlite
  pooled connections occasionally serve a request from a connection that has not
  yet observed the commit made microseconds earlier on another connection — so
  `verify-email` can transiently 401 (token row not yet visible) or `login` can
  transiently 403 (`email_verified_at` not yet visible). The final DB state is
  always consistent; this is a setup-only timing artifact, never seen by real
  users who have human think-time. The builder therefore retries those two steps
  with a small backoff (`_post_expecting`). This robustness is in the **setup**
  code only — it does **not** touch the measured NFR-01 request path.
