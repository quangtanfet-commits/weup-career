# ADR-006: Docker Strategy

**Status:** Accepted  
**Date:** 2026-05-27  

---

## Decision

Use **multi-stage Docker builds** for both backend and frontend, with distinct `development` and `production` Docker Compose configurations.

---

## Multi-Stage Build Rationale

### Backend: 2-stage

**Stage 1 (builder):** `python:3.12-slim` + build tools + `uv pip install`
**Stage 2 (runtime):** `python:3.12-slim` — copy only installed packages; no pip, no gcc, no build tools

**Benefits:**
- Final image: ~180MB (vs ~800MB naive build)
- No build tools available to exploits in the runtime layer
- Reproducible: `uv` locks to exact versions

**Security hardening in runtime stage:**
- `RUN adduser --disabled-password appuser && chown -R appuser /app`
- `USER appuser` — non-root execution
- `COPY --chown=appuser:appuser` all files
- No `COPY . .` — explicit layer ordering for Docker cache optimization

### Frontend: 2-stage

> **Cập nhật (ADR-014, 2026-05-30):** frontend chuyển từ Vite SPA static sang **Next.js 15 (App Router)**. Runtime stage nay là **Node.js** (`next start`), không phải nginx static — vì các route công khai Điều 5a render server-side (RSC/ISR) để SEO. Mô tả nginx-static bên dưới là **lịch sử**; topology hiện hành xem [deployment.md §Frontend Dockerfile](../architecture/deployment.md).

**Stage 1 (builder):** `node:20-alpine` + `npm ci` + `npm run build` (`next build`, standalone)
**Stage 2 (runtime):** `node:20-alpine` — copy `.next/standalone` + `.next/static` + `public/`; `CMD node server.js`

**Benefits:**
- Final image: ~140MB (Node runtime cần thiết cho RSC/ISR)
- Nginx đứng trước làm reverse-proxy + TLS + cache static assets; **không** còn `try_files $uri /index.html` SPA-fallback (Next.js tự routing server-side)

---

## Development vs Production Compose

### Development
- Bind-mount source code (hot reload without rebuild)
- Override `CMD` to dev server / uvicorn with `--reload`
- No TLS (localhost)
- Relaxed CORS
- DEBUG logging

### Production
- Images pulled from GHCR (immutable, tagged by git SHA)
- No bind mounts
- TLS via Let's Encrypt certs in volume
- Strict CORS
- INFO logging
- Docker secrets cho `SECRET_KEY` **và `FIELD_ENCRYPTION_KEY`** (mã hóa kết quả trắc nghiệm) — không dùng env var

---

## Image Tagging Strategy

```
:latest            → DO NOT USE in production (non-deterministic)
:sha-a1b2c3d       → CI builds (immutable, traceable to commit)
:v1.2.3            → Release tags (promoted from sha- tag after testing)
:main              → Latest main branch build (staging only)
```

---

## Consequences

- `docker compose up` starts full stack in one command (DX requirement)
- `docker compose -f docker-compose.yml -f docker-compose.prod.yml up` for production overrides
- Health checks in Dockerfile (not just compose): `HEALTHCHECK CMD curl -f http://localhost:8000/api/v1/health`
- `.dockerignore` excludes: `.git`, `__pycache__`, `*.pyc`, `node_modules`, `tests/`, `docs/`, `.env*`
