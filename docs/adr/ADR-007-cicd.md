# ADR-007: CI/CD Design

**Status:** Accepted  
**Date:** 2026-05-27  

---

## Decision

**Use GitHub Actions** with a parallel quality gate strategy. All gates must pass before merge. Production deployment requires manual approval.

---

## Pipeline Design

### On every PR push

```yaml
jobs:
  lint-backend:     # mypy --strict, ruff, bandit
  lint-frontend:    # tsc --noEmit, eslint, prettier --check
  test-backend:     # pytest --cov --cov-fail-under=95
  test-frontend:    # vitest run --coverage
  security-scan:    # trivy (images + fs), semgrep, pip-audit, npm audit
  e2e:              # playwright test (chromium + firefox + webkit)
  
  # All run in parallel; merge blocked if any fails
```

### On merge to main

```yaml
jobs:
  build-images:     # docker buildx, push to GHCR with :sha-XXXX
  deploy-staging:   # docker compose pull + up on staging server
  smoke-tests:      # curl health/ready, run abbreviated Playwright suite
  
  # If smoke passes, release is promotable
```

### Release (manual tag push)

```yaml
jobs:
  deploy-production: # environment: production (requires approval in GitHub UI)
                     # Pulls :sha-XXXX image, retags as :vX.Y.Z
                     # docker compose up on production server
```

---

## Quality Gate Details

| Gate | Tool | Fail Threshold |
|------|------|----------------|
| Python types | `mypy --strict` | Any error |
| Python lint | `ruff check` | Any error |
| Python security lint | `bandit -ll` | HIGH severity |
| Backend tests | `pytest --cov-fail-under=95` | <95% line coverage |
| Frontend types | `tsc --noEmit` | Any error |
| Frontend lint | `eslint --max-warnings 0` | Any warning |
| Frontend tests | `vitest --coverage --coverage-lines 95` | <95% line coverage |
| Container scan | `trivy image --severity HIGH,CRITICAL` | Any HIGH or CRITICAL CVE |
| Dependency audit | `pip-audit` + `npm audit --audit-level high` | Any HIGH+ vulnerability |
| SAST | `semgrep --config p/python p/react p/security` | Any finding |
| E2E | Playwright (all 3 browsers) | Any failure |
| OpenAPI schema | `openapi-spec-validator` | Invalid schema |

---

## Secrets Management in CI

- `SECRET_KEY`, `POSTGRES_PASSWORD` (future) → GitHub repository secrets
- Never in Dockerfile, never in git history
- Rotation procedure: update GitHub secret → redeploy

---

## Caching Strategy

- Python: cache `~/.cache/uv` by `pyproject.toml` hash
- Node: cache `~/.npm` by `package-lock.json` hash
- Docker layers: `--cache-from type=registry,ref=ghcr.io/org/todo:buildcache`

Reduces PR gate time from ~8min → ~2min after warm cache.

---

## Consequences

- `main` branch is always deployable (protected branch; no direct push)
- Every commit to main triggers a staging deploy (continuous delivery)
- Production deployments are deliberate (require human approval)
- Rollback: `docker compose down && docker compose up` with previous image tag
