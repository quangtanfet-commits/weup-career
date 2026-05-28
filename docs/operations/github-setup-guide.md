# GitHub Repository Setup Guide

**Date:** 2026-05-28  
**Status:** Ready to push — local commit `11ba742` exists

---

## Step 1: Create GitHub Repository

### Option A — GitHub CLI (recommended)
```bash
# Authenticate first
gh auth login

# Create public or private repo
gh repo create weup-career \
  --private \
  --description "WeUp Career — nền tảng hướng nghiệp cho học sinh và người đi làm tại Việt Nam (FastAPI + React + TypeScript)" \
  --homepage "https://your-domain.com"
```

### Option B — GitHub Web UI
1. Go to https://github.com/new
2. Repository name: `weup-career`
3. Visibility: Private (recommended)
4. Do NOT initialize with README (we have our own)
5. Click "Create repository"

---

## Step 2: Push to GitHub

```bash
# Set remote origin
git remote add origin https://github.com/YOUR_USERNAME/weup-career.git

# Push main branch
git push -u origin main

# Verify
git remote -v
git log --oneline
```

---

## Step 3: Configure Branch Protection

Go to: **Settings → Branches → Add rule**

Branch name pattern: `main`

Apply these settings (see `.github/branch-protection.md` for full details):
- ✅ Require pull request before merging (1 approval)
- ✅ Require status checks to pass (all CI jobs)
- ✅ Require branches to be up to date
- ✅ Do not allow bypassing

---

## Step 4: Add Repository Secrets

Go to: **Settings → Secrets and variables → Actions**

```
STAGING_HOST      = IP or hostname of staging server
STAGING_USER      = SSH username (e.g. deploy)
STAGING_SSH_KEY   = Private SSH key (-----BEGIN OPENSSH PRIVATE KEY-----)
PROD_HOST         = IP or hostname of production server  
PROD_USER         = SSH username
PROD_SSH_KEY      = Private SSH key
CODECOV_TOKEN     = From codecov.io (optional)
```

---

## Step 5: Configure GitHub Environments

Go to: **Settings → Environments**

### Create `staging` environment:
- No approval required
- Add variable: `STAGING_URL = https://staging.yourdomain.com`

### Create `production` environment:
- ✅ Required reviewers: [your GitHub username]
- Deployment branches: `main` only
- Add variable: `PRODUCTION_URL = https://yourdomain.com`

---

## Step 6: Enable Security Features

Go to: **Settings → Security**

- ✅ Dependency graph: Enable
- ✅ Dependabot alerts: Enable
- ✅ Dependabot security updates: Enable
- ✅ Code scanning: Enable (uses CodeQL from our workflow)
- ✅ Secret scanning: Enable

---

## Step 7: Enable GitHub Packages (GHCR)

Docker images are published to GitHub Container Registry automatically by CI.

Go to: **Settings → Packages** → ensure GHCR is enabled.

First push sets image visibility. Set to **Private** initially:
```bash
# After first CI run, set image visibility:
gh api \
  -X PATCH \
  /user/packages/container/weup-career%2Fbackend/versions/LATEST_ID \
  -f visibility=private
```

---

## Step 8: Set Up Notifications

Go to: **Settings → Notifications** → Configure for:
- Failed CI runs → Email
- Dependabot alerts → Email
- Security advisories → Email

---

## Workflow After Setup

```bash
# Daily development workflow
git checkout -b feat/my-feature
# ... make changes ...
git add .
git commit -m "feat: add feature description"
git push -u origin feat/my-feature

# Open PR in GitHub UI → CI runs automatically → get review → merge
```

---

## Quick Verification Checklist

After setup, verify:
- [ ] `git push -u origin main` succeeds
- [ ] Branch protection rules active (try direct push to main — should fail)
- [ ] CI workflow appears in Actions tab on next push
- [ ] Dependabot shows in Security tab
- [ ] GHCR shows backend/frontend packages after first CI run
