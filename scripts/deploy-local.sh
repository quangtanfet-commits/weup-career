#!/usr/bin/env bash
# WeUp Career — local build & deploy (no GitHub CI/CD required).
#
# Brings up the full production-like topology on this machine:
#   nginx (:80) ──/api/*──▶ backend  (FastAPI, :8000)
#               └──/──────▶ frontend (Next.js standalone, :3000 internal)
#
# It provisions backend/.env with real random secrets on first run, builds both
# Docker images from source, starts the stack, waits for health, and runs smoke
# checks. No GitHub Actions / remote registry involved — everything is local.
#
# Usage:
#   scripts/deploy-local.sh [up|build|down|logs|status|smoke]   (default: up)
#     up      build images, start stack, wait healthy, smoke-test  (default)
#     build   build images only (also bootstraps backend/.env)
#     down    stop and remove the stack containers
#     logs    follow logs from all services
#     status  show container status
#     smoke   run smoke checks against a running stack
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.local.yml)
BACKEND_ENV="backend/.env"
BACKEND_ENV_EXAMPLE="backend/.env.example"
BASE_URL="http://localhost"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-240}"

log() { printf '\033[0;36m[deploy-local]\033[0m %s\n' "$*"; }
err() { printf '\033[0;31m[deploy-local] ERROR:\033[0m %s\n' "$*" >&2; }
die() { err "$*"; exit 1; }

compose() { docker compose "${COMPOSE_FILES[@]}" "$@"; }

require_tools() {
  command -v docker >/dev/null 2>&1 || die "docker not found on PATH."
  docker compose version >/dev/null 2>&1 || die "docker compose v2 plugin not found."
  command -v openssl >/dev/null 2>&1 || die "openssl not found (needed to generate secrets)."
  command -v curl >/dev/null 2>&1 || die "curl not found (needed for health/smoke checks)."
}

# Ensure KEY=<32-byte hex> exists in backend/.env. A missing key, an empty
# value, a value shorter than 32 chars, or an obvious placeholder is replaced
# with a fresh `openssl rand -hex 32`. Both keys are required by the backend's
# Settings (Field(min_length=32)) or pydantic raises at boot.
ensure_secret() {
  local key="$1" file="$2" val fresh
  val="$(grep -E "^${key}=" "$file" 2>/dev/null | head -1 | cut -d= -f2- || true)"
  if [ -z "$val" ] || [ "${#val}" -lt 32 ] \
    || printf '%s' "$val" | grep -qiE 'change|placeholder|your-|example|xxxx'; then
    fresh="$(openssl rand -hex 32)"
    if grep -qE "^${key}=" "$file" 2>/dev/null; then
      grep -vE "^${key}=" "$file" > "${file}.tmp"
      printf '%s=%s\n' "$key" "$fresh" >> "${file}.tmp"
      mv "${file}.tmp" "$file"
    else
      printf '%s=%s\n' "$key" "$fresh" >> "$file"
    fi
    log "generated ${key} in ${file}"
  fi
}

bootstrap_env() {
  if [ ! -f "$BACKEND_ENV" ]; then
    if [ -f "$BACKEND_ENV_EXAMPLE" ]; then
      cp "$BACKEND_ENV_EXAMPLE" "$BACKEND_ENV"
      log "created ${BACKEND_ENV} from example"
    else
      : > "$BACKEND_ENV"
      log "created empty ${BACKEND_ENV}"
    fi
  fi
  ensure_secret SECRET_KEY "$BACKEND_ENV"
  ensure_secret FIELD_ENCRYPTION_KEY "$BACKEND_ENV"
}

wait_healthy() {
  log "waiting for stack to become healthy (timeout ${HEALTH_TIMEOUT}s)…"
  local deadline=$(( $(date +%s) + HEALTH_TIMEOUT ))
  until curl -sf "${BASE_URL}/api/v1/health" >/dev/null 2>&1; do
    [ "$(date +%s)" -ge "$deadline" ] && { compose ps; die "backend did not become healthy within ${HEALTH_TIMEOUT}s"; }
    sleep 3
  done
  log "backend healthy."
  until curl -sf "${BASE_URL}/" >/dev/null 2>&1; do
    [ "$(date +%s)" -ge "$deadline" ] && { compose ps; die "frontend did not respond through nginx within ${HEALTH_TIMEOUT}s"; }
    sleep 3
  done
  log "frontend reachable through nginx."
}

smoke() {
  log "running smoke checks against ${BASE_URL}…"
  curl -sf "${BASE_URL}/api/v1/health" >/dev/null || die "health endpoint failed"
  curl -sf "${BASE_URL}/api/v1/ready"  >/dev/null || die "ready endpoint failed"
  curl -sf "${BASE_URL}/" | grep -q "<!DOCTYPE html>" || die "frontend did not return HTML"
  log "smoke checks passed ✓"
}

cmd_up() {
  require_tools
  bootstrap_env
  log "building images (frontend + backend) from source…"
  compose build
  log "starting stack (detached)…"
  compose up -d
  wait_healthy
  smoke
  cat <<EOF

  WeUp Career is running locally:
    App         ${BASE_URL}
    API docs    ${BASE_URL}/api/v1/docs
    Backend     http://localhost:8000  (direct)

  Logs:   scripts/deploy-local.sh logs
  Status: scripts/deploy-local.sh status
  Stop:   scripts/deploy-local.sh down
EOF
}

case "${1:-up}" in
  up)     cmd_up ;;
  build)  require_tools; bootstrap_env; compose build ;;
  down)   compose down ;;
  logs)   compose logs -f --tail=100 ;;
  status) compose ps ;;
  smoke)  require_tools; smoke ;;
  *)      die "unknown command '${1}'. Use: up | build | down | logs | status | smoke" ;;
esac
