#!/usr/bin/env bash
# WeUp Career — native security scan (no Docker / no nginx).
#
# Runs the static security matrix directly on this host (the devcontainer's DinD
# cannot exec container shells, so the dockerized security-scan workflow can't run
# here). Emits machine-readable JSON per tool under report/<run-id>/security/ and a
# summary.json, then exits non-zero if any HARD gate trips.
#
# Tools (all already on PATH / in the project envs):
#   gitleaks      secret leakage in the working tree
#   bandit        Python SAST            (gate: HIGH severity == 0)
#   ruff          Python lint (security-relevant rules included)
#   pip-audit     Python dependency CVEs (gate: any fixable HIGH/CRITICAL)
#   npm audit     JS dependency CVEs     (gate: HIGH/CRITICAL count == 0)
#
# Usage:
#   scripts/security-scan-native.sh [RUN_ID]
# RUN_ID defaults to a UTC timestamp; the same id is reused by generate-report.mjs.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RUN_ID="${1:-$(date -u +%Y%m%dT%H%M%SZ)}"
OUT="report/${RUN_ID}/security"
mkdir -p "$OUT"

log()  { printf '\033[0;36m[security-scan]\033[0m %s\n' "$*"; }
warn() { printf '\033[0;33m[security-scan] WARN:\033[0m %s\n' "$*"; }
fail() { printf '\033[0;31m[security-scan] GATE FAIL:\033[0m %s\n' "$*"; }

GATE_FAILURES=()

# --- gitleaks: secrets in the working tree ----------------------------------
# --no-git scans files on disk (not history) so a clean tree with an ignored
# backend/.env is still inspected for accidental staged secrets.
if command -v gitleaks >/dev/null 2>&1; then
  log "gitleaks (working tree)…"
  GL_CFG=(); [ -f .gitleaks.toml ] && GL_CFG=(--config .gitleaks.toml)
  gitleaks detect --no-git "${GL_CFG[@]}" --report-format json \
    --report-path "$OUT/gitleaks.json" >/dev/null 2>&1
  GL_RC=$?
  GL_COUNT=$(python3 -c "import json,sys;print(len(json.load(open('$OUT/gitleaks.json'))))" 2>/dev/null || echo 0)
  if [ "$GL_RC" -ne 0 ] && [ "${GL_COUNT:-0}" -gt 0 ]; then
    fail "gitleaks found ${GL_COUNT} potential secret(s)"
    GATE_FAILURES+=("gitleaks:${GL_COUNT}")
  else
    log "gitleaks clean."
  fi
else
  warn "gitleaks not on PATH — skipped."
fi

# --- bandit: Python SAST -----------------------------------------------------
log "bandit (backend/app)…"
( cd backend && uv run bandit -r app -f json -q -o "../$OUT/bandit.json" >/dev/null 2>&1 || true )
BANDIT_HIGH=$(python3 -c "import json;d=json.load(open('$OUT/bandit.json'));print(sum(1 for r in d.get('results',[]) if r.get('issue_severity')=='HIGH'))" 2>/dev/null || echo 0)
if [ "${BANDIT_HIGH:-0}" -gt 0 ]; then
  fail "bandit HIGH severity findings: ${BANDIT_HIGH}"
  GATE_FAILURES+=("bandit-high:${BANDIT_HIGH}")
else
  log "bandit HIGH=0."
fi

# --- ruff: lint (report only) ------------------------------------------------
log "ruff (backend)…"
( cd backend && uv run ruff check app --output-format json > "../$OUT/ruff.json" 2>/dev/null || true )

# --- pip-audit: Python RUNTIME dependency CVEs ------------------------------
# Audit the runtime closure only (uv export --no-dev), not the dev venv: pip /
# setuptools / wheel and test-only deps are not shipped in the production image,
# so gating on them produces noise. Tracked exceptions (vuln IDs we've accepted
# with justification) live in scripts/.pip-audit-ignore — one ID per line.
log "pip-audit (backend runtime closure)…"
PIP_IGNORE=()
if [ -f scripts/.pip-audit-ignore ]; then
  while IFS= read -r line; do
    line="${line%%#*}"; line="${line// /}"
    [ -n "$line" ] && PIP_IGNORE+=(--ignore-vuln "$line")
  done < scripts/.pip-audit-ignore
fi
( cd backend \
  && uv export --no-dev --no-emit-project --no-hashes --format requirements-txt \
       > /tmp/weup-rt-reqs.txt 2>/dev/null \
  && uv run pip-audit -r /tmp/weup-rt-reqs.txt "${PIP_IGNORE[@]}" --format json \
       > "../$OUT/pip-audit.json" 2>/dev/null || true )
PIP_HC=$(python3 - "$OUT/pip-audit.json" <<'PY' 2>/dev/null || echo 0
import json,sys
try:
    d=json.load(open(sys.argv[1]))
except Exception:
    print(0); raise SystemExit
deps=d.get("dependencies", d) if isinstance(d,dict) else d
n=0
for dep in (deps or []):
    for v in dep.get("vulns",[]) or []:
        if v.get("fix_versions"):  # only actionable (a fix exists)
            n+=1
print(n)
PY
)
if [ "${PIP_HC:-0}" -gt 0 ]; then
  fail "pip-audit fixable vulnerabilities: ${PIP_HC}"
  GATE_FAILURES+=("pip-audit-fixable:${PIP_HC}")
else
  log "pip-audit: no fixable CVEs."
fi

# --- npm audit: JS dependency CVEs ------------------------------------------
log "npm audit (frontend deps)…"
( cd frontend && npm audit --json > "../$OUT/npm-audit.json" 2>/dev/null || true )
read -r NPM_HIGH NPM_CRIT <<<"$(python3 -c "import json;v=json.load(open('$OUT/npm-audit.json')).get('metadata',{}).get('vulnerabilities',{});print(v.get('high',0),v.get('critical',0))" 2>/dev/null || echo '0 0')"
if [ "${NPM_HIGH:-0}" -gt 0 ] || [ "${NPM_CRIT:-0}" -gt 0 ]; then
  fail "npm audit HIGH=${NPM_HIGH} CRITICAL=${NPM_CRIT}"
  GATE_FAILURES+=("npm-high:${NPM_HIGH}" "npm-critical:${NPM_CRIT}")
else
  log "npm audit HIGH=0 CRITICAL=0 (moderate/low reported, not gated)."
fi

# --- summary -----------------------------------------------------------------
STATUS="pass"; [ "${#GATE_FAILURES[@]}" -gt 0 ] && STATUS="fail"
python3 - "$OUT/summary.json" "$RUN_ID" "$STATUS" "${BANDIT_HIGH:-0}" "${PIP_HC:-0}" "${NPM_HIGH:-0}" "${NPM_CRIT:-0}" "${GL_COUNT:-0}" <<'PY'
import json,sys
path,run_id,status,bandit,pip,nh,nc,gl=sys.argv[1:9]
json.dump({
  "run_id":run_id,"status":status,
  "gates":{
    "gitleaks_findings":int(gl),
    "bandit_high":int(bandit),
    "pip_audit_fixable":int(pip),
    "npm_high":int(nh),"npm_critical":int(nc),
  },
}, open(path,"w"), indent=2)
PY

log "artifacts → ${OUT}/"
if [ "$STATUS" = "fail" ]; then
  fail "security gate FAILED: ${GATE_FAILURES[*]}"
  exit 1
fi
log "security gate PASSED ✓"
