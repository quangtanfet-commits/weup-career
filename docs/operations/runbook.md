# Operations Runbook

**Version:** 1.0.0 | **Date:** 2026-05-27  
**Audience:** Operators, On-call Engineers  

---

## Quick Reference

```bash
# Service status
docker compose ps
docker compose logs -f backend
docker compose logs -f nginx

# Health checks
curl http://localhost/api/v1/health
curl http://localhost/api/v1/ready

# Restart a service
docker compose restart backend

# Full restart (preserve data)
docker compose down && docker compose up -d

# Force rebuild (after image update)
docker compose pull && docker compose up -d
```

---

## Runbook 1: Deploying a New Version

```bash
# 1. Pull latest images
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull

# 2. Graceful rolling restart (downtime < 30s)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps backend

# 3. Run smoke tests
./scripts/smoke-test.sh

# 4. If smoke tests fail — rollback
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d \
  --no-deps backend \
  --image ghcr.io/org/weup-career-backend:PREVIOUS_SHA

# 5. Verify rollback
./scripts/smoke-test.sh
```

---

## Runbook 2: Database Recovery

### Symptom: Backend returns 503

```bash
# Check DB file exists
ls -la /var/lib/todo/data/app.db

# Check DB integrity
sqlite3 /var/lib/todo/data/app.db "PRAGMA integrity_check;"
# Expected: "ok"

# If corrupted — restore from backup
cp /var/lib/todo/backup/app.db.latest /var/lib/todo/data/app.db
docker compose restart backend

# Verify
curl http://localhost/api/v1/ready
```

### Symptom: SQLite database locked

```bash
# Identify processes holding the lock
lsof /var/lib/todo/data/app.db

# If stale lock from crashed process
docker compose restart backend
```

---

## Runbook 3: High 5xx Error Rate

```bash
# 1. Check recent error logs
docker compose logs --since=15m backend | grep '"level":"error"' | jq .

# 2. Check for OOM kills
docker stats --no-stream
docker inspect todo_backend_1 | jq '.[0].State'

# 3. If OOM — increase memory limit in docker-compose.prod.yml
# Default: 512MB; increase to 1GB

# 4. Restart if process is unhealthy
docker compose restart backend

# 5. Escalate to on-call if errors persist after restart
```

---

## Runbook 4: Rotating JWT Secret Key

**Impact:** All existing access tokens become invalid. All users are logged out.

```bash
# 1. Generate new secret key
openssl rand -hex 32 > /tmp/new_secret_key.txt

# 2. Update Docker secret
# (Steps depend on deployment environment)
# docker-compose: update ./secrets/secret_key.txt

# 3. Restart backend (picks up new secret)
docker compose restart backend

# 4. Verify health
curl http://localhost/api/v1/health

# 5. Notify users (email / status page)
# "We've updated our security infrastructure. Please log in again."
```

---

## Runbook 5: Rate Limit False Positives

**Symptom:** Legitimate user getting 429 Too Many Requests

```bash
# Check rate limit logs
docker compose logs --since=15m nginx | grep "limiting requests"

# Temporary workaround — whitelist IP in nginx config
# Edit nginx/nginx.prod.conf — add to rate limit zone bypass

# Permanent fix: adjust per-user limits in slowapi config
# Requires backend redeploy

# Check if IP is a NAT (shared IP behind corporate proxy)
# Consider increasing per-IP limits or using per-user limits
```

---

## Runbook 6: Backup Procedure

```bash
#!/bin/bash
# scripts/backup.sh — run daily via cron

DATE=$(date +%Y%m%d-%H%M%S)
SRC=/var/lib/todo/data/app.db
BACKUP_DIR=/var/lib/todo/backup

# SQLite hot backup (safe while DB is running due to WAL mode)
sqlite3 $SRC ".backup '$BACKUP_DIR/app.db.$DATE'"

# Rotate: keep last 7 daily backups
ls -t $BACKUP_DIR/app.db.* | tail -n +8 | xargs rm -f

echo "Backup complete: $BACKUP_DIR/app.db.$DATE"
```

```bash
# Restore from backup
cp /var/lib/todo/backup/app.db.YYYYMMDD-HHMMSS /var/lib/todo/data/app.db
docker compose restart backend
curl http://localhost/api/v1/ready
```

---

## Monitoring Checklist (Daily)

```bash
# 1. All services running?
docker compose ps | grep -v "Up"  # Should return nothing

# 2. Disk usage OK?
df -h /var/lib/todo/data/

# 3. Any errors in last 24h?
docker compose logs --since=24h backend | grep '"level":"error"' | wc -l
# Alert if > 100

# 4. Health endpoints responsive?
curl -f http://localhost/api/v1/health
curl -f http://localhost/api/v1/ready

# 5. Backup ran?
ls -la /var/lib/todo/backup/ | head -5
```

---

## Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| 5xx error rate | >0.1% | >1% | Check logs, restart if unresponsive |
| p99 latency | >500ms | >2000ms | Check DB query times |
| Memory usage | >400MB | >500MB | Restart backend, check for leak |
| Disk usage | >70% | >85% | Rotate logs, move old backups |
| Failed health checks | 2 consecutive | 5 consecutive | Page on-call |
