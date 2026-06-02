#!/usr/bin/env bash
# WeUp Career — N-1 native load test (Gate C, NFR-01).
# See docs/performance/n1-load-test-2026-06.md.
#
# Boots an EPHEMERAL, hermetic backend (own DB copy, FileMailer outbox, rate
# limiting OFF) on a dedicated port so it never clobbers the developer's :8000
# dev backend, then runs Locust headless in two phases:
#
#   Phase 1 — warm-up + cohort build: test_start mints a real adult cohort
#             (register→verify via outbox→login→submit RIASEC→generate reco) and
#             persists it; a short load warms SQLite page cache + import cost.
#             Stats discarded.
#   Phase 2 — measured baseline: reuse the cohort, ramp 0→200 then steady, with
#             --reset-stats so the ramp is excluded from the percentiles.
#
# Artifacts land under report/<run-id>/loadtest/. The script prints a verdict
# against NFR-01 (read p99<150ms, write p99<300ms, err<0.1%) but does NOT edit
# docs/spec.md — ticking Gate C is a deliberate manual step after review.
#
# Usage:   scripts/run-loadtest-native.sh [RUN_ID]
# Env:
#   LT_BACKEND_PORT   ephemeral backend port (default 8100; NOT 8000)
#   COHORT_SIZE       accounts to mint for the VU pool (default 50)
#   RUN_USERS         peak concurrent users (default 200 — the NFR-01 target)
#   SPAWN_RATE        users spawned per second (default 4 ⇒ ~50s ramp)
#   RUN_TIME          measured run duration incl. ramp (default 6m)
#   WARMUP_TIME       warm-up duration (default 90s)
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RUN_ID="${1:-$(date -u +%Y%m%dT%H%M%SZ)}"
OUT="report/${RUN_ID}/loadtest"
mkdir -p "$OUT"

LT_BACKEND_PORT="${LT_BACKEND_PORT:-8100}"
COHORT_SIZE="${COHORT_SIZE:-50}"
RUN_USERS="${RUN_USERS:-200}"
SPAWN_RATE="${SPAWN_RATE:-4}"
RUN_TIME="${RUN_TIME:-6m}"
WARMUP_TIME="${WARMUP_TIME:-90s}"
HOST="http://localhost:${LT_BACKEND_PORT}"
COHORT_FILE="$REPO_ROOT/$OUT/cohort.json"

log()  { printf '\033[0;36m[loadtest]\033[0m %s\n' "$*"; }
warn() { printf '\033[0;33m[loadtest] WARN:\033[0m %s\n' "$*"; }
fail() { printf '\033[0;31m[loadtest] FAIL:\033[0m %s\n' "$*"; }

# --- run metadata ------------------------------------------------------------
COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
BRANCH="$(git branch --show-current 2>/dev/null || echo unknown)"
python3 - "$OUT/meta.json" "$RUN_ID" "$COMMIT" "$BRANCH" "$RUN_USERS" "$SPAWN_RATE" "$RUN_TIME" <<'PY'
import json, sys
path, run_id, commit, branch, users, rate, dur = sys.argv[1:8]
json.dump({"run_id": run_id, "commit": commit, "branch": branch,
           "profile": "n1-load-baseline (native, single-node SQLite)",
           "users": int(users), "spawn_rate": float(rate), "run_time": dur},
          open(path, "w"), indent=2)
PY

# --- ephemeral backend (hermetic DB, FileMailer outbox, rate limit off) ------
if curl -sf "${HOST}/api/v1/health" >/dev/null 2>&1; then
  fail "something is already listening on :${LT_BACKEND_PORT}; set LT_BACKEND_PORT to a free port."
  exit 1
fi

export WEUP_MAILER_OUTBOX="$REPO_ROOT/$OUT/outbox.ndjson"
: >"$WEUP_MAILER_OUTBOX"

# Hermetic DB: copy the seeded dev DB and upgrade to head, so the load backend
# has the current schema without mutating backend/data/app.db. A single
# DATABASE_URL override redirects both alembic and the app at the copy.
LT_DB="$REPO_ROOT/$OUT/app.db"
if [ -f backend/data/app.db ]; then
  cp backend/data/app.db "$LT_DB"
else
  rm -f "$LT_DB"  # no seed → alembic upgrade creates it fresh
fi
export DATABASE_URL="sqlite+aiosqlite:///$LT_DB"
log "upgrading run-scoped load-test DB to head…"
( cd backend && uv run alembic upgrade head ) >"$OUT/db-migrate.log" 2>&1
if [ $? -ne 0 ]; then
  fail "DB migration failed (see ${OUT}/db-migrate.log)"; exit 1
fi

# setsid so `kill -- -PGID` reaps the uv-run wrapper AND the forked uvicorn.
# RATE_LIMIT_ENABLED=false: a 200-VU run blows past the register/login buckets;
# the limiter is a product invariant owned by pytest, not the latency subject.
log "starting ephemeral backend on :${LT_BACKEND_PORT} (rate limiting off, FileMailer outbox)…"
setsid bash -c "cd '$REPO_ROOT/backend' && export RATE_LIMIT_ENABLED=false && exec uv run uvicorn app.main:get_app --factory --port ${LT_BACKEND_PORT}" \
  >"$OUT/backend.log" 2>&1 &
BACKEND_PGID=$!
trap '[ "${BACKEND_PGID:-0}" -ne 0 ] && kill -- -"$BACKEND_PGID" 2>/dev/null' EXIT

for _ in $(seq 1 60); do
  curl -sf "${HOST}/api/v1/health" >/dev/null 2>&1 && break
  sleep 1
done
if ! curl -sf "${HOST}/api/v1/health" >/dev/null 2>&1; then
  fail "backend never became ready on :${LT_BACKEND_PORT} (see ${OUT}/backend.log)"; exit 1
fi
log "backend ready."

LOCUST=(uv run --project backend locust -f backend/loadtest/locustfile.py --headless --host "$HOST")

# --- Phase 1: warm-up + cohort build (stats discarded) -----------------------
log "phase 1 — warm-up + building ${COHORT_SIZE}-account cohort (this mints real accounts; takes a bit)…"
"${LOCUST[@]}" -u "$RUN_USERS" -r "$SPAWN_RATE" -t "$WARMUP_TIME" \
  --cohort-size "$COHORT_SIZE" --cohort-file "$COHORT_FILE" \
  --csv "$OUT/warmup" --csv-full-history \
  >"$OUT/warmup.log" 2>&1
if [ $? -ne 0 ]; then
  fail "warm-up phase failed (see ${OUT}/warmup.log)"; exit 1
fi
log "phase 1 done (cohort persisted to cohort.json)."

# --- Phase 2: measured baseline (--reset-stats excludes the ramp) ------------
log "phase 2 — measured baseline: ${RUN_USERS} users, ramp @ ${SPAWN_RATE}/s, ${RUN_TIME} (steady measured)…"
"${LOCUST[@]}" -u "$RUN_USERS" -r "$SPAWN_RATE" -t "$RUN_TIME" --reset-stats \
  --cohort-file "$COHORT_FILE" \
  --csv "$OUT/baseline" --csv-full-history \
  >"$OUT/baseline.log" 2>&1
LOCUST_RC=$?
if [ "$LOCUST_RC" -ne 0 ]; then
  warn "measured run exited ${LOCUST_RC} (see ${OUT}/baseline.log) — verdict below may be partial."
fi

# --- teardown ----------------------------------------------------------------
kill -- -"$BACKEND_PGID" 2>/dev/null; wait "$BACKEND_PGID" 2>/dev/null
BACKEND_PGID=0; trap - EXIT

# --- verdict against NFR-01 --------------------------------------------------
log "verdict (NFR-01: read p99<150ms, write p99<300ms, err<0.1%):"
python3 - "$OUT/baseline_stats.csv" "$OUT/verdict.json" <<'PY'
import csv, json, sys

stats_csv, verdict_path = sys.argv[1], sys.argv[2]
READ = {
    "GET /me/assessments/[id]", "GET /careers", "GET /careers/[id]",
    "GET /recommendations/[id]", "GET /auth/me",
}
WRITE = {"POST /assessments/riasec/submit", "POST /recommendations"}

rows = []
try:
    with open(stats_csv, newline="") as fh:
        rows = list(csv.DictReader(fh))
except FileNotFoundError:
    print("  no baseline_stats.csv — run produced no stats")
    json.dump({"status": "error", "reason": "no stats csv"}, open(verdict_path, "w"))
    sys.exit(2)

def p99(r):  # Locust column header is "99%"
    v = r.get("99%") or r.get("99%ile") or "0"
    try: return float(v)
    except ValueError: return 0.0

groups = {"read": {"slo": 150.0, "rows": []}, "write": {"slo": 300.0, "rows": []}}
total_req = total_fail = 0
for r in rows:
    name = r.get("Name", "")
    if r.get("Type", "").strip() in ("", "Aggregated") and name == "Aggregated":
        total_req = int(float(r.get("Request Count", 0) or 0))
        total_fail = int(float(r.get("Failure Count", 0) or 0))
        continue
    if name in READ: groups["read"]["rows"].append(r)
    elif name in WRITE: groups["write"]["rows"].append(r)

ok = True
report = {}
for g, info in groups.items():
    worst = max((p99(r) for r in info["rows"]), default=0.0)
    passed = worst < info["slo"] and bool(info["rows"])
    ok = ok and passed
    report[g] = {"worst_p99_ms": worst, "slo_ms": info["slo"],
                 "verdict": "PASS" if passed else "FAIL",
                 "endpoints": {r["Name"]: p99(r) for r in info["rows"]}}
    print(f"  {g:5s} group worst p99 = {worst:7.1f} ms  (SLO {info['slo']:.0f})  -> "
          f"{'PASS' if passed else 'FAIL'}")
    for r in info["rows"]:
        print(f"        {r['Name']:34s} p99={p99(r):7.1f} ms  n={r.get('Request Count')}")

err_rate = (total_fail / total_req * 100.0) if total_req else 0.0
err_ok = err_rate < 0.1
ok = ok and err_ok
print(f"  error-rate = {err_rate:.4f}%  ({total_fail}/{total_req})  -> {'PASS' if err_ok else 'FAIL'}")
print(f"  OVERALL: {'PASS' if ok else 'FAIL'}")

report.update({"error_rate_pct": err_rate, "total_requests": total_req,
               "total_failures": total_fail, "status": "pass" if ok else "fail"})
json.dump(report, open(verdict_path, "w"), indent=2)
sys.exit(0 if ok else 1)
PY
VERDICT_RC=$?

echo
log "artifacts → ${OUT}/ (baseline_stats.csv, verdict.json, *.log, cohort.json)"
exit "$VERDICT_RC"
