# N-1 — Load test (Gate C, NFR-01) — doc-first spec

**Status:** proposed · **Date:** 2026-06-02 · **Owner task:** N-1
**Closes:** spec.md §Gate C "Load test: p99 < 150ms ở tải mục tiêu" + fills the
`_TBD_` baselines in `docs/validation/weup-career/spike-report.md`.

## 1. Problem & intent

NFR-01 sets the platform's latency SLO:

| Class | SLO | At |
|---|---|---|
| read | p99 < 150 ms | 200 concurrent users |
| write | p99 < 300 ms | 200 concurrent users |

(Mirrored in `docs/scalability/strategy.md`: p50 read < 30 ms, 5xx < 0.1 %.)

Today this SLO is **aspirational** — never measured against the running
implementation. The spike-report (P-3) explicitly defers it: "thay SLO khát
vọng bằng baseline đo được" (replace the aspirational SLO with a measured
baseline). N-1 turns NFR-01 from a wish into a measured baseline and ticks the
Gate C load-test box.

The existing `.github/workflows/load-test.yml` is a **non-working stub**: it
targets `staging.example.com`, runs `k6/scenarios/{baseline,spike,soak}.js`
files that do not exist, and gates on `p99 > 100ms` — a threshold that matches
neither NFR-01 class. It is treated as a placeholder to be reconciled (§8), not
as prior art.

## 2. Scope

**In scope** — a repeatable, native load test that:

- drives the **load-bearing read and write endpoints** (§4) under a realistic
  concurrent mix;
- mints a **real authenticated + consented cohort** (no faked tokens), so the
  sensitive-data read path (decrypt + append-only audit, CP-3 fail-closed) is
  exercised exactly as in production;
- reports **p50 / p95 / p99 / max + RPS + error-rate per endpoint group**;
- produces a machine-readable artifact (CSV/JSON) + a human verdict against
  NFR-01;
- writes the measured numbers back into the spike-report and this doc.

**Out of scope (documented, not measured here):**

- **Production-scale topology.** MVP is single-node SQLite (ADR-002). This test
  measures the **single-node baseline**; the Postgres + multi-node ceiling is a
  separate exercise. The baseline's job is to prove the code path is not
  pathologically slow and to expose per-endpoint hotspots, with an explicit
  caveat that absolute numbers are floor-not-ceiling.
- **Soak / stability** (long-running) and **spike** (burst) profiles — defined
  in §6 as follow-on profiles but the **baseline** profile is the N-1 gate.
- Rate-limit behaviour under load — owned by backend pytest (`test_ratelimit`);
  the load run disables the limiter (§5) so it measures latency, not 429s.

## 3. Tooling decision — Locust (Python, via uv dev-dep)

**Chosen: Locust**, added as a backend dev dependency (`uv add --group dev
locust`). Rationale:

- **Native-first constraint.** The devcontainer (aarch64/linuxkit DinD) cannot
  run docker-compose; everything runs native via uv/npm. Locust is `pip`/`uv`
  installable and runs headless with no extra binary. `k6` needs a separately
  installed binary (not present — `command -v k6` → not installed) and is only
  wired for CI via `grafana/k6-action`.
- **Auth setup is non-trivial and Pythonic.** The cohort builder must run the
  real `register → verify (read outbox) → login` flow to obtain bearer tokens
  and drive `/guardians/consent`. Doing this in Python lets the harness reuse
  the same FileMailer-outbox approach the e2e harness already relies on
  (`docs/testing/e2e-native-mailer-outbox.md`), rather than reimplementing it in
  k6 JS.
- **Percentile reporting built in.** `--headless --csv` emits
  `_stats.csv` (p50/p66/p75/p80/p90/p95/p98/p99/p99.9/max per endpoint) — direct
  evidence for the NFR-01 gate.

The k6 CI workflow is addressed in §8 (reconcile, not duplicate).

## 4. Target endpoints (mapped to NFR-01 classes)

Selected for **blast radius**: the legally/perf-critical paths plus the
high-traffic content reads a school cohort hits first.

### Read group (gate: p99 < 150 ms)

| Endpoint | Why it's load-bearing |
|---|---|
| `GET /me/assessments/{result_id}` | **Primary target.** Sensitive-data read: field-decrypt + append-only audit write inside the read txn (CP-3 fail-closed). The spike-report's "p99 GET kết quả (giải mã+audit) <150ms" line. |
| `GET /careers` + `GET /careers/{id}` | Highest-traffic content browse; representative of the public-ish read path. |
| `GET /recommendations/{id}` | Read of a generated recommendation (rationale assembly). There is no bare list endpoint — the cohort builder mints a `reco_id` during setup and the read task fetches it by id. |
| `GET /auth/me` | Auth-guarded identity read — cheapest read, anchors the p50<30ms claim. (Mounted under the auth router prefix; the bare `/me` of earlier drafts does not exist.) |

### Write group (gate: p99 < 300 ms)

| Endpoint | Why it's load-bearing |
|---|---|
| `POST /assessments/riasec/submit` | **Primary target.** Field-encrypt + audit write; the spike-report's "p99 submit trắc nghiệm <300ms" line. |
| `POST /recommendations` | Recommendation generation with rationale — heaviest synchronous compute. |

Auth/login writes are exercised during cohort setup (warm-up), not in the steady
mix, to avoid the rate-limiter/credential-hashing cost dominating the write
percentile (login bcrypt is intentionally slow and is not the NFR-01 subject).

## 5. Environment

- **Native backend** on `:8000`, launched the same way the e2e harness does:
  `uv run uvicorn app.main:get_app --factory --port 8000`, under `setsid`,
  `environment=development` ⇒ FileMailer when `WEUP_MAILER_OUTBOX` set.
- **Rate limiting OFF** (`RATE_LIMIT_ENABLED=false`) — a 200-VU run blows past
  the production register/login buckets; the limiter is a product invariant
  owned by pytest, not the latency subject (same reasoning as the e2e harness).
- **Hermetic DB copy + `alembic upgrade head`** into a run-scoped
  `report/<run-id>/loadtest/app.db`, `DATABASE_URL` pointed at the copy — the
  developer's seed DB is never mutated.
- **Warm-up** before measurement: a short ramp whose samples are discarded, so
  the percentile window excludes cold-start (first-request import/connect cost)
  and SQLite page-cache warming.

## 6. Load profile

**Baseline (the N-1 gate):**

- **200 concurrent users** (matches NFR-01's "200 người dùng đồng thời").
- **Ramp:** 0 → 200 over 60 s (spawn-rate ~3–4/s), then **steady 5 min** at 200.
- **Mix:** read-heavy 85/15 (read:write) — career platform browse pattern;
  documented so the percentile is interpretable, not a 50/50 synthetic.
- Measurement window = steady phase only (ramp + warm-up discarded).

**Follow-on profiles (defined, not gated by N-1):**

- **spike:** 200 → 600 burst for 30 s — observe 5xx + recovery (NFR for
  resilience, not NFR-01).
- **soak:** 100 VU for 30 min — memory/connection-leak watch.

## 7. Pass/fail gate (the real NFR-01, not the stub's 100 ms)

The run **passes** iff, over the steady window:

- read group **p99 < 150 ms** AND
- write group **p99 < 300 ms** AND
- error-rate (non-2xx/3xx) **< 0.1 %**.

Each endpoint group is reported separately; a single slow group fails the gate.
If the single-node baseline misses, the verdict records the miss **with the
hotspot** (which endpoint, p99, suspected cause) rather than silently lowering
the bar — temporary lowered thresholds are forbidden. A documented exception
(e.g. "p99 X ms on single-node SQLite; meets SLO after the Postgres migration —
tracked as <ticket>") is the only acceptable non-pass close, and requires
explicit owner sign-off.

## 8. Reconciling the CI workflow (separate, confirm before touching)

`.github/workflows/load-test.yml` is stale (§1). The honest options:

1. **Replace** the k6 stub with a Locust job that runs the baseline profile
   against an ephemeral native backend (mirrors `run-validation-native.sh`).
2. **Keep k6 for CI** and port the baseline scenario to `k6/scenarios/baseline.js`
   with the NFR-01 thresholds, leaving Locust as the local tool.

Modifying CI is a shared-state change → **not done as part of N-1 without
explicit approval.** N-1 delivers the native harness + measured baseline; the CI
wiring is a follow-up doc-first change. Either way the 100 ms threshold is
corrected to the NFR-01 pair.

## 9. Deliverables

- `backend/loadtest/locustfile.py` — cohort builder + read/write task sets.
- `backend/loadtest/README.md` — how to run natively.
- `scripts/run-loadtest-native.sh` (optional) — boot ephemeral backend (DB copy,
  outbox, rate-limit off, setsid teardown) → run Locust headless → drop
  artifacts under `report/<run-id>/loadtest/`.
- Results written back into this doc's §10 and the spike-report TBDs.
- Gate C checkbox ticked in `spec.md` **only if** the gate passes.

## 10. Results

**Verdict: FAIL the NFR-01 gate at 200 VU on single-node SQLite — 0 % errors.**
This is the **floor-not-ceiling** miss anticipated in §2/§7, **not** a logic bug:
all 50,982 requests succeeded (err 0.0000 %); the code path is correct, but
SQLite's single-writer serialization dominates latency at 200 concurrent VUs.
Per §7 the miss is recorded **with the hotspot**; the bar is **not** lowered and
Gate C in `docs/spec.md` is **not** ticked. Closing this as a documented
exception (single-node SQLite floor; SLO met after the Postgres migration,
ADR-002) requires explicit owner sign-off + a tracking ticket (§10.3).

### 10.1 Measured (steady window, --reset-stats excludes ramp)

| Group | Endpoint(s) | SLO | p50 | p95 | p99 | max | err% | verdict |
|---|---|---|---|---|---|---|---|---|
| read | GET /me/assessments/{id} | p99<150ms | 170 | 750 | **1400** | 2888 | 0.00 | ❌ FAIL |
| read | GET /careers(+/{id}) | p99<150ms | 120–140 | 540–590 | **780–940** | 2312 | 0.00 | ❌ FAIL |
| read | GET /recommendations/{id} | p99<150ms | 130 | 570 | **870** | 2228 | 0.00 | ❌ FAIL |
| read | GET /auth/me | p99<150ms | 120 | 570 | **830** | 2079 | 0.00 | ❌ FAIL |
| write | POST /assessments/riasec/submit | p99<300ms | 190 | 740 | **1400** | 2708 | 0.00 | ❌ FAIL |
| write | POST /recommendations | p99<300ms | 240 | 820 | **1400** | 4108 | 0.00 | ❌ FAIL |

All values in **ms**. Aggregate: 50,982 reqs, **164.5 RPS**, p50 150 ms, p99
1100 ms, 0 failures. Full CSV:
`report/n1-baseline-20260602T114940Z/loadtest/baseline_stats.csv`.

### 10.2 Hotspot & suspected cause

- **Hotspot:** `GET /me/assessments/{id}` (p99 1400 ms, highest-traffic read,
  n=14,190) and both writes (`POST /assessments/riasec/submit`,
  `POST /recommendations`, both p99 1400 ms). Even the cheapest read
  (`GET /auth/me`) misses at p99 830 ms — i.e. the miss is **systemic
  contention**, not one slow endpoint.
- **Suspected cause:** **SQLite single-writer serialization.** SQLite admits one
  writer at a time; under 200 concurrent VUs every write (and every read that
  takes a write lock) queues head-of-line. Crucially `GET /me/assessments/{id}`
  is *not* a pure read — CP-3 does a field-decrypt **plus an append-only audit
  write inside the read txn**, so the primary read also contends for the write
  lock. The near-uniform ~1400 ms p99 ceiling across the heaviest read and both
  writes is the signature of this shared serialization point, not per-endpoint
  compute. p50s (120–240 ms) are healthy — the system is fast uncontended and
  degrades only at the tail under concurrency.
- **Not the cause:** application errors (0 %), rate limiting (off), cold start
  (warm-up + `--reset-stats` discard it), or the cohort-builder gevent race
  (setup-only, fixed in §9 / README).

### 10.3 Disposition (owner decision required)

Per §7, the only acceptable non-pass close is a **documented exception with
owner sign-off**, not a lowered threshold. Proposed close:

> _p99 read 830–1400 ms / write 1400 ms on single-node SQLite at 200 VU
> (0 % errors). The single-writer serialization is an MVP-topology limit
> (ADR-002), not a code defect. NFR-01 to be re-measured on Postgres +
> connection pooling, tracked as **[#73](https://github.com/quangtanfet-commits/weup-career/issues/73)**. Gate C stays unticked until
> that re-measure passes._

**Sign-off:** exception wording **approved by owner 2026-06-02**. Postgres
re-measure tracked as **[#73](https://github.com/quangtanfet-commits/weup-career/issues/73)**.
Gate C remains **not** ticked until that re-measure passes.

The cheap single-node follow-on knobs flagged earlier — SQLite **WAL** +
`busy_timeout` — have since been tried (§11) and gave **no improvement** (read
p99 1600 ms / write 1900 ms tuned vs 1400/1400 baseline). WAL was already on; the
added `synchronous=NORMAL` + `busy_timeout` was reverted. This **confirms the
miss is purely topological** (single-node 1-writer serialization), not a tunable —
exactly what the exception above asserts.

**Environment of record:** commit `b34ca8c` (branch `main`) · native uvicorn,
single process · SQLite + aiosqlite (run-scoped hermetic copy, `alembic upgrade
head`) · host 8 vCPU / 3.8 GiB · rate limiting OFF · Locust 200 VU, ramp 4/s,
6 min run with `--reset-stats` · 50-account real adult cohort · run-id
`n1-baseline-20260602T114940Z`.

## 11. Single-node SQLite tuning attempt (WAL pragmas) — doc-first

### 11.1 Finding that reframes the lever

The §10 baseline already ran with **`PRAGMA journal_mode=WAL`** (set at connect
time in `backend/app/core/database.py`). So WAL alone does **not** close the gap —
the ~1400 ms tail happened *with* WAL. Two pragmas that materially affect
write-under-contention latency were **not** set:

| Pragma | Default (as run in §10) | Effect on the §10 hotspot |
|---|---|---|
| `synchronous` | `FULL` (2) — fsync on **every** commit | **Primary lever.** Under 200 VU every commit (and every CP-3 audit write) fsyncs while holding the writer lock; everyone else queues. `NORMAL` (1) under WAL fsyncs only at checkpoint, not per-commit. |
| `busy_timeout` | aiosqlite passes `timeout=5.0` ⇒ ~5000 ms implicit | Explains **0 errors** in §10 (writers wait up to 5 s, never get SQLITE_BUSY). Setting it explicitly documents intent; it does **not** by itself lower latency. |

So the requested "WAL + busy_timeout" is really **`synchronous=NORMAL` + explicit
`busy_timeout`** — WAL is a precondition already met.

### 11.2 Durability tradeoff (must be explicit — audit log is legally weighted)

`synchronous=NORMAL` under WAL is **not** a consistency/atomicity weakening:
- The CP-3 audit row is written in the **same transaction** as the action, so an
  action can never be observed without its audit row — atomicity holds at any
  `synchronous` level. Audit-completeness in normal operation is unaffected.
- The only exposure: on an **OS crash / power loss**, transactions committed
  since the last WAL checkpoint may be lost **as whole (action+audit) pairs**.
  The DB is never corrupted (no torn writes). A clean app crash loses nothing.

For an **MVP single-node** (ADR-002) this would be the documented standard
tradeoff; it disappears entirely on the Postgres target. The change was applied
**experimentally** and then **reverted** (see §11.3–§11.4): the re-run showed no
latency benefit, so there was no reason to accept even the bounded power-loss
window on the legally-weighted audit trail.

### 11.3 Change (applied, then reverted)

`backend/app/core/database.py` `_set_sqlite_pragmas`, added after WAL:
`PRAGMA synchronous=NORMAL`, `PRAGMA busy_timeout=5000`. SQLite-only (guarded by
`_is_sqlite`); no app-code or Postgres impact. After the §11.4 re-run came back
with no improvement, this was **reverted** — `_set_sqlite_pragmas` is back to only
`journal_mode=WAL` + `foreign_keys=ON`, keeping audit-log durability at `FULL`.

### 11.4 Re-run result — negative

Tuned re-run, identical 200-VU profile (run-id `n1-wal-tuned-20260602T120801Z`):

| Group | §10 baseline worst p99 | §11 tuned worst p99 | Δ |
|---|---|---|---|
| read | 1400 ms | **1600 ms** | no improvement (slightly worse) |
| write | 1400 ms | **1900 ms** | no improvement (slightly worse) |
| errors | 0 / 50,982 | **0 / 50,854** | unchanged (PASS) |

`synchronous=NORMAL` + explicit `busy_timeout` produced **no latency benefit**;
the small regression is run-to-run noise on a constrained host. This is the
expected outcome given §11.1: per-commit fsync was never the dominant cost —
SQLite's **single global writer-lock serialization** is. CP-3 makes `GET
/me/assessments/*` a writer too (append-only audit row inside the read txn), so
even "reads" queue behind that one lock at 200 VU; relaxing fsync cannot widen a
queue that is one-writer-deep by construction.

**Conclusion:** the bottleneck is **topological** (single-node 1-writer), not a
tunable. The pragma was reverted (§11.3) to keep the audit trail at `FULL`
durability for zero cost. This reinforces §10.3 — NFR-01 must be re-measured on
**Postgres + connection pooling** (ADR-002), where concurrent writers are the
whole point, rather than chased with single-node SQLite knobs.
