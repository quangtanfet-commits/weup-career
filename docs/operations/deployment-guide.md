# Deployment Guide

**Version:** 1.0.0 | **Date:** 2026-05-27

---

## Prerequisites

- Docker Engine 24.x
- Docker Compose v2.x
- Git
- (Production) A server with:
  - 1+ vCPU, 2GB RAM, 20GB disk
  - Ports 80 and 443 open
  - A domain name pointing to the server

---

## Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/org/todo-app.git
cd todo-app

# 2. Copy environment template
cp .env.example .env
# Edit .env: set SECRET_KEY to a random value

# 3. Start all services
docker compose up --build

# App available at: http://localhost
# API docs at:       http://localhost/api/v1/docs
# Backend logs:      docker compose logs -f backend
```

**First run:** Alembic migrations run automatically on backend startup.

---

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SECRET_KEY` | Yes | JWT signing key (32+ chars random) | `openssl rand -hex 32` |
| `DATABASE_URL` | No | SQLAlchemy async URL | `sqlite+aiosqlite:////data/app.db` |
| `ENVIRONMENT` | No | `development` / `production` | `production` |
| `LOG_LEVEL` | No | `debug` / `info` / `warning` | `info` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Access token lifetime | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | Refresh token lifetime | `7` |
| `RATE_LIMIT_AUTH_REQUESTS` | No | Auth rate limit (req/min) | `20` |
| `CORS_ORIGINS` | No | Comma-separated allowed origins | `https://app.example.com` |
| `ALLOWED_HOSTS` | No | Comma-separated allowed hosts | `app.example.com` |

---

## Production Deployment

### Step 1: Server Setup

```bash
# On your server
apt-get update && apt-get install -y docker.io docker-compose-v2 git

# Create deployment user
useradd -m -s /bin/bash deploy
usermod -aG docker deploy

# Create data directory
mkdir -p /var/lib/todo/{data,backup,certs,secrets}
chown -R deploy:deploy /var/lib/todo
```

### Step 2: Deploy Application

```bash
# As deploy user
cd /home/deploy
git clone https://github.com/org/todo-app.git
cd todo-app

# Generate and store secret key
openssl rand -hex 32 > /var/lib/todo/secrets/secret_key.txt
chmod 600 /var/lib/todo/secrets/secret_key.txt

# Configure production overrides
cp docker-compose.prod.yml.example docker-compose.prod.yml
# Edit: set your domain, image versions
```

### Step 3: TLS Certificate (Let's Encrypt)

```bash
# Using Certbot
docker run --rm -v /var/lib/todo/certs:/etc/letsencrypt \
  certbot/certbot certonly \
  --standalone \
  --email admin@example.com \
  --agree-tos \
  -d app.example.com

# Auto-renewal cron
echo "0 12 * * * certbot renew --quiet && docker compose restart nginx" | crontab -
```

### Step 4: Start Services

```bash
cd /home/deploy/todo-app

# Start
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify
docker compose ps
curl https://app.example.com/api/v1/health
```

---

## Database Migrations

```bash
# Migrations run automatically on backend startup
# To run manually:
docker compose exec backend alembic upgrade head

# Check migration status
docker compose exec backend alembic current

# Rollback one migration
docker compose exec backend alembic downgrade -1

# Create new migration (after model changes)
docker compose exec backend alembic revision --autogenerate -m "add due_date to todo"
```

---

## CI/CD Automated Deployment

Every merge to `main` triggers:
1. Tests pass → build Docker image → tag as `sha-XXXX`
2. Push to GHCR
3. SSH to staging → `docker compose pull && docker compose up -d`
4. Smoke tests against staging
5. Tag image as `main` after smoke tests pass

Production deployment:
1. Requires manual approval in GitHub Actions
2. Tags the tested image as `vX.Y.Z`
3. Deploys to production server
4. Runs smoke tests

---

## Rollback Procedure

```bash
# List available versions
docker images ghcr.io/org/todo-backend --format "table {{.Tag}}\t{{.CreatedAt}}"

# Rollback to previous SHA
export PREVIOUS_SHA=sha-a1b2c3d
sed -i "s|todo-backend:.*|todo-backend:${PREVIOUS_SHA}|" docker-compose.prod.yml
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps backend

# Verify
curl https://app.example.com/api/v1/health
```

---

## Post-Deployment Verification

```bash
#!/bin/bash
# scripts/smoke-test.sh

set -e
BASE_URL="${1:-http://localhost}"

echo "Testing health..."
curl -sf "$BASE_URL/api/v1/health" | jq '.status' | grep '"ok"'

echo "Testing readiness..."
curl -sf "$BASE_URL/api/v1/ready" | jq '.status' | grep '"ready"'

echo "Testing static assets..."
curl -sf "$BASE_URL/" | grep -q "<!DOCTYPE html>"

echo "Testing API reachability..."
curl -sf "$BASE_URL/api/v1/auth/register" -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke@test.local","password":"SecurePass123"}' \
  | jq '.email' | grep "smoke@test.local"

echo "All smoke tests passed ✓"
```
