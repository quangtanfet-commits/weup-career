# Branch Protection Configuration Guide

Configure these settings in GitHub → Settings → Branches after creating the repository.

## `main` branch protection rules

| Setting | Value | Reason |
|---------|-------|--------|
| Require pull request before merging | ✅ Yes | No direct pushes to main |
| Required approvals | **1** | At least one peer review |
| Dismiss stale reviews on new commits | ✅ Yes | Re-review if code changes after approval |
| Require review from CODEOWNERS | ✅ Yes | Auth changes require security team |
| Require status checks to pass | ✅ Yes | CI must be green |
| Required status checks | See below | |
| Require branches to be up to date | ✅ Yes | No merging stale branches |
| Require conversation resolution | ✅ Yes | All comments addressed |
| Require signed commits | ✅ Yes (recommended) | Verify author identity |
| Do not allow bypassing | ✅ Yes | Even admins go through PRs |
| Allow force pushes | ❌ No | |
| Allow deletions | ❌ No | |

## Required Status Checks

Add ALL of these as required checks:

```
✅ 🔍 Backend Lint & Types
✅ 🔍 Frontend Lint & Types
✅ 🧪 Backend Tests
✅ 🧪 Frontend Tests
✅ 🔒 Security Scan
✅ 🎭 E2E Tests — chromium
✅ 🎭 E2E Tests — firefox
✅ 🎭 E2E Tests — webkit
✅ ✅ CI Gate — All Passed
```

## GitHub Environments

### `staging`
- No approval required (auto-deploy on merge to main)
- Environment URL: your staging domain
- Secrets: STAGING_HOST, STAGING_USER, STAGING_SSH_KEY

### `production`
- **Required reviewers**: minimum 1 (team lead)
- **Wait timer**: 0 minutes
- **Deployment branches**: only `main` + version tags `v*`
- Environment URL: your production domain
- Secrets: PROD_HOST, PROD_USER, PROD_SSH_KEY

## Repository Secrets (Settings → Secrets → Actions)

| Secret | Description |
|--------|-------------|
| `STAGING_HOST` | Staging server IP/hostname |
| `STAGING_USER` | SSH user for staging |
| `STAGING_SSH_KEY` | Private SSH key for staging |
| `PROD_HOST` | Production server IP/hostname |
| `PROD_USER` | SSH user for production |
| `PROD_SSH_KEY` | Private SSH key for production |
| `CODECOV_TOKEN` | Codecov upload token (optional) |

## Repository Variables (Settings → Variables → Actions)

| Variable | Description |
|----------|-------------|
| `STAGING_URL` | e.g. `https://staging.yourdomain.com` |
| `PRODUCTION_URL` | e.g. `https://yourdomain.com` |
