#!/usr/bin/env bash
# WeUp Career — native full-stack validation run (no Docker / no nginx).
#
# Drives every suite directly on the host (the devcontainer's DinD cannot run
# the dockerized compose stack) and aggregates the machine-readable output into
# a single report/<run-id>/index.html via scripts/generate-report.mjs.
#
# Steps (each is fault-tolerant: a suite failure is recorded, not fatal, so the
# HTML report is always produced; the script's FINAL exit code is the overall
# gate — non-zero if any suite or the security matrix failed).
#
#   1. backend   pytest + JUnit XML + coverage JSON
#   2. frontend  vitest + JSON + v8 json-summary coverage
#   3. e2e       playwright (default: chromium) + JSON reporter
#   4. security  scripts/security-scan-native.sh (shares the run-id)
#   5. report    scripts/generate-report.mjs
#
# Usage:
#   scripts/run-validation-native.sh [RUN_ID]
# Env:
#   PW_PROJECT   playwright project filter (default: chromium; "" = all 3)
#   SKIP_E2E=1   skip the playwright step (fast inner loop)
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RUN_ID="${1:-$(date -u +%Y%m%dT%H%M%SZ)}"
OUT="report/${RUN_ID}"
mkdir -p "$OUT/backend" "$OUT/frontend" "$OUT/e2e" "$OUT/security" "$OUT/storybook" "$OUT/tla"

PW_PROJECT="${PW_PROJECT-chromium}"

log()  { printf '\033[0;36m[validate]\033[0m %s\n' "$*"; }
warn() { printf '\033[0;33m[validate] WARN:\033[0m %s\n' "$*"; }
fail() { printf '\033[0;31m[validate] FAIL:\033[0m %s\n' "$*"; }

FAILURES=()

# --- run metadata ------------------------------------------------------------
COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
BRANCH="$(git branch --show-current 2>/dev/null || echo unknown)"
PYVER="$(cd backend && uv run python -c 'import sys;print(sys.version.split()[0])' 2>/dev/null || echo '?')"
python3 - "$OUT/meta.json" "$RUN_ID" "$COMMIT" "$BRANCH" "$PYVER" "$(node --version)" <<'PY'
import json,sys
path,run_id,commit,branch,py,node=sys.argv[1:7]
json.dump({"run_id":run_id,"commit":commit,"branch":branch,
           "python":py,"node":node,"profile":"full-stack (native)"},
          open(path,"w"), indent=2)
PY

# --- 1. backend --------------------------------------------------------------
log "backend pytest (+junit +coverage json)…"
( cd backend && uv run pytest \
    --junitxml="../$OUT/backend/junit.xml" \
    --cov=app --cov-report="json:../$OUT/backend/coverage.json" \
    >"../$OUT/backend/pytest.log" 2>&1 )
BACK_RC=$?
if [ "$BACK_RC" -ne 0 ]; then
  fail "backend pytest exit ${BACK_RC} (see ${OUT}/backend/pytest.log)"
  FAILURES+=("backend:${BACK_RC}")
else
  log "backend pytest passed."
fi

# --- 2. frontend unit --------------------------------------------------------
log "frontend vitest (+json +coverage)…"
( cd frontend && npx vitest run \
    --reporter=json --outputFile="../$OUT/frontend/vitest.json" \
    --coverage --coverage.provider=v8 \
    --coverage.reporter=json-summary --coverage.reporter=text \
    --coverage.reportsDirectory="../$OUT/frontend" \
    >"../$OUT/frontend/vitest.log" 2>&1 )
FE_RC=$?
if [ "$FE_RC" -ne 0 ]; then
  fail "frontend vitest exit ${FE_RC} (see ${OUT}/frontend/vitest.log)"
  FAILURES+=("frontend:${FE_RC}")
else
  log "frontend vitest passed."
fi

# --- 2b. storybook build (gap 5) ---------------------------------------------
# Headless build-storybook is deterministic and needs no external service, so it
# runs in the native gate (a broken story / primitive API drift fails here).
# Chromatic visual regression is CI-only — it needs the external
# CHROMATIC_PROJECT_TOKEN (see docs/testing/chromatic.md), so it is NOT run here.
log "storybook headless build…"
SB_START=$(date +%s%3N 2>/dev/null || echo 0)
( cd frontend && npm run build-storybook >"../$OUT/storybook/build.log" 2>&1 )
SB_RC=$?
SB_END=$(date +%s%3N 2>/dev/null || echo 0)
SB_STORIES=$(ls frontend/components/ui/*.stories.tsx 2>/dev/null | wc -l | tr -d ' ')
python3 - "$OUT/storybook/summary.json" "$SB_RC" "$SB_START" "$SB_END" "$SB_STORIES" <<'PY'
import json,sys
path,rc,start,end,stories=sys.argv[1:6]
dur=(int(end)-int(start)) if start!="0" and end!="0" else None
json.dump({"status":"pass" if rc=="0" else "fail",
           "stories":int(stories),"duration_ms":dur},
          open(path,"w"), indent=2)
PY
if [ "$SB_RC" -ne 0 ]; then
  fail "storybook build exit ${SB_RC} (see ${OUT}/storybook/build.log)"
  FAILURES+=("storybook:${SB_RC}")
else
  log "storybook build passed."
fi

# --- 3. e2e ------------------------------------------------------------------
# Run against a PRODUCTION build on a dedicated port (default 3100), never the
# dev server. `next dev` compiles routes on first hit, so under parallel workers
# the cold-compile latency blows past Playwright's 30s test timeout → flaky
# "timedOut" failures that are environmental, not real. A prebuilt `next start`
# serves settled routes deterministically. The user's :3000 dev server is left
# untouched. Backend stays at :8000 (the prod build fetches it the same way).
if [ "${SKIP_E2E:-0}" = "1" ]; then
  warn "SKIP_E2E=1 — skipping playwright."
else
  E2E_PORT="${E2E_PORT:-3100}"
  # Same-origin API for the browser: build with a RELATIVE public API base so
  # client fetches hit ":${E2E_PORT}/api/v1/*", and run with E2E_PROXY_API=1 so
  # next.config rewrites those to the host backend (:8000). This mirrors nginx
  # in production and sidesteps the dev-only CORS allowlist (the prod build on
  # :3100 is cross-origin to :8000 otherwise → preflight blocked → auth fails).
  log "frontend production build (for deterministic e2e, same-origin /api)…"
  ( cd frontend && NEXT_PUBLIC_API_BASE_URL="" E2E_PROXY_API=1 \
      npm run build >"../$OUT/e2e/build.log" 2>&1 )
  BUILD_RC=$?
  if [ "$BUILD_RC" -ne 0 ]; then
    fail "frontend build exit ${BUILD_RC} (see ${OUT}/e2e/build.log)"
    FAILURES+=("e2e-build:${BUILD_RC}")
  else
    log "starting next start on :${E2E_PORT}…"
    ( cd frontend && E2E_PROXY_API=1 \
        npx next start -p "$E2E_PORT" >"../$OUT/e2e/server.log" 2>&1 ) &
    E2E_SRV_PID=$!
    # Wait up to 60s for the prod server to accept connections.
    for _ in $(seq 1 60); do
      curl -sf "http://localhost:${E2E_PORT}" >/dev/null 2>&1 && break
      sleep 1
    done
    log "playwright e2e (project=${PW_PROJECT:-all}, base=:${E2E_PORT})…"
    PW_ARGS=(); [ -n "$PW_PROJECT" ] && PW_ARGS=(--project="$PW_PROJECT")
    # CI=1 makes playwright.config skip its own webServer block (we manage the
    # prod server here) and enables retries=2; --reporter=json overrides github.
    ( cd frontend && CI=1 E2E_BASE_URL="http://localhost:${E2E_PORT}" \
        npx playwright test "${PW_ARGS[@]}" --reporter=json \
        >"../$OUT/e2e/playwright.json" 2>"../$OUT/e2e/playwright.log" )
    E2E_RC=$?
    kill "$E2E_SRV_PID" 2>/dev/null; wait "$E2E_SRV_PID" 2>/dev/null
    if [ "$E2E_RC" -ne 0 ]; then
      fail "playwright exit ${E2E_RC} (see ${OUT}/e2e/playwright.log)"
      FAILURES+=("e2e:${E2E_RC}")
    else
      log "playwright e2e passed."
    fi
  fi
fi

# --- 3b. formal verification (TLA+/TLC) --------------------------------------
# Two gates per /formal-verify:
#   Gate A  — model check each MC spec: the spec is internally correct
#             (TLC reports "No error has been found").
#   Sabotage — each <M>Sab spec breaks one impl predicate on purpose; TLC MUST
#             report a violation. A sabotage run that stays green means the
#             invariant is too weak (false confidence) and fails the gate.
# Fault-tolerant like the other suites: a TLC miss is recorded in FAILURES, not
# fatal, so the HTML report is still produced. Per-module logs land in
# $OUT/tla/<M>.{mc,sab}.log and the parsed rollup in $OUT/tla/summary.json.
log "formal verification (TLA+/TLC: 6 modules, Gate A + sabotage)…"
TLA_JAR="${TLA_JAR:-/usr/local/share/tla/tla2tools.jar}"
TLA_CM="${TLA_CM:-/opt/specula/lib/CommunityModules-deps.jar}"
TLA_MODULES=(ConsentLifecycle SensitiveDataAccess AuthorizationModel \
             RecommendationGovernance AuthTokenLifecycle CompetencyProgress)
if [ ! -f "$TLA_JAR" ]; then
  warn "tla2tools.jar not found at ${TLA_JAR} — skipping TLA+/TLC gate."
  python3 - "$OUT/tla/summary.json" <<'PY'
import json,sys
json.dump({"status":"skip","reason":"tla2tools.jar not found","modules":[]},
          open(sys.argv[1],"w"), indent=2)
PY
else
  ( cd tla
    for m in "${TLA_MODULES[@]}"; do
      java -cp "$TLA_JAR:$TLA_CM" tlc2.TLC -config "$m.cfg" "${m}MC.tla" \
        >"../$OUT/tla/${m}.mc.log" 2>&1
      java -cp "$TLA_JAR:$TLA_CM" tlc2.TLC -config "${m}Sab.cfg" "${m}Sab.tla" \
        >"../$OUT/tla/${m}.sab.log" 2>&1 || true
    done
    # TLC dumps <M>Sab_TTrace_*.{tla,bin} on each violation; they regenerate
    # every run and are gitignored — drop them so the working tree stays clean.
    rm -f ./*_TTrace_*.tla ./*_TTrace_*.bin 2>/dev/null || true )
  # Parse logs → summary.json. Exit non-zero iff any Gate A failed OR any
  # sabotage was NOT caught. The module→CP map mirrors tla/README.md.
  python3 - "$OUT/tla" <<'PY'
import json,os,re,sys
out=sys.argv[1]
CP={"ConsentLifecycle":["CP-1","CP-2"],"SensitiveDataAccess":["CP-3"],
    "AuthorizationModel":["CP-4"],"RecommendationGovernance":["CP-5","CP-6"],
    "AuthTokenLifecycle":["CP-7"],"CompetencyProgress":["CP-8"]}
order=["ConsentLifecycle","SensitiveDataAccess","AuthorizationModel",
       "RecommendationGovernance","AuthTokenLifecycle","CompetencyProgress"]
def read(p):
    try: return open(p,encoding="utf-8",errors="replace").read()
    except FileNotFoundError: return ""
mods=[]; ok=True
for m in order:
    mc=read(os.path.join(out,f"{m}.mc.log"))
    sab=read(os.path.join(out,f"{m}.sab.log"))
    gate_a = "No error has been found" in mc
    sab_caught = ("is violated" in sab) or ("Error: Invariant" in sab)
    sm=re.search(r"(\d+) states generated, (\d+) distinct states found", mc)
    dm=re.search(r"depth of the complete state graph search is (\d+)", mc)
    distinct=int(sm.group(2)) if sm else None
    depth=int(dm.group(1)) if dm else None
    if not gate_a or not sab_caught: ok=False
    mods.append({"module":m,"cp":CP[m],
                 "gate_a":"pass" if gate_a else "fail",
                 "distinct_states":distinct,"depth":depth,
                 "sabotage":"caught" if sab_caught else "missed"})
json.dump({"status":"pass" if ok else "fail","modules":mods},
          open(os.path.join(out,"summary.json"),"w"), indent=2)
sys.exit(0 if ok else 1)
PY
  TLA_RC=$?
  if [ "$TLA_RC" -ne 0 ]; then
    fail "formal verification gate failed (see ${OUT}/tla/*.log)"
    FAILURES+=("tla:${TLA_RC}")
  else
    log "formal verification passed (Gate A + 6/6 sabotage caught)."
  fi
fi

# --- 4. security -------------------------------------------------------------
log "security matrix…"
./scripts/security-scan-native.sh "$RUN_ID" >"$OUT/security/scan.log" 2>&1
SEC_RC=$?
if [ "$SEC_RC" -ne 0 ]; then
  fail "security gate failed (see ${OUT}/security/scan.log)"
  FAILURES+=("security:${SEC_RC}")
else
  log "security gate passed."
fi

# --- 5. report ---------------------------------------------------------------
log "generating HTML report…"
node scripts/generate-report.mjs "$RUN_ID"

echo
if [ "${#FAILURES[@]}" -gt 0 ]; then
  fail "validation FAILED: ${FAILURES[*]}"
  log "report → ${OUT}/index.html"
  exit 1
fi
log "validation PASSED ✓ — report → ${OUT}/index.html"
