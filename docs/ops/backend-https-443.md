# Local HTTPS dev listener for the backend (:443)

**Status:** accepted · **Date:** 2026-06-03 · **Scope:** local devcontainer only — not CI, not production

## Problem

The backend runs natively inside the aarch64/linuxkit DinD devcontainer as
`uv run uvicorn app.main:get_app --factory --port 8000`, bound to
`127.0.0.1:8000`. The developer wants to reach the backend **from the Mac mini
host over HTTPS on the conventional port `:443`** (e.g. to open `/api/v1/docs`
or hit the API directly with TLS), mirroring the frontend which already serves
on `:80`.

Two facts shape the solution:

1. `net.ipv4.ip_unprivileged_port_start=0` in the container, so uid 1000 can
   bind `:443` directly — no root, no `cap_net_bind_service`.
2. VS Code Dev Containers auto-forwards any listener to the host's `localhost`,
   so a process on `0.0.0.0:443` surfaces as `https://localhost` on the Mac.

The backend has **no TLS configured** and uvicorn serves one port per process.

## Decision

Run a **second uvicorn instance** of the same `get_app()` factory with TLS on
`0.0.0.0:443`, alongside the untouched plaintext `127.0.0.1:8000` instance.

Rationale:

- **Keep `:8000` as-is.** The `:80` frontend dev server calls the backend at
  `http://localhost:8000` (`NEXT_PUBLIC_API_BASE_URL` default). Adding a port
  rather than moving one means nothing existing breaks.
- **Second process, not a TLS proxy.** No extra dependency (stunnel/socat/nginx
  unavailable in this native flow); uvicorn already links OpenSSL 3.0.13. Both
  instances share `backend/data/app.db` — acceptable for single-developer dev
  load.
- **Self-signed cert** under `backend/certs/` (gitignored). SAN covers
  `localhost` + `127.0.0.1`. Browsers show a one-time trust prompt; `curl` needs
  `-k`. This is a dev convenience endpoint, not a production trust anchor.

### Details

- **Cert generation** (one-off, regenerable; 825-day validity is the
  browser-accepted max for local certs):
  ```bash
  cd backend
  openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout certs/key.pem -out certs/cert.pem \
    -days 825 -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
  ```
- **HTTPS listener** (cwd `backend/`):
  ```bash
  CORS_ORIGINS="http://localhost,http://localhost:3000,https://localhost" \
  uv run uvicorn app.main:get_app --factory \
    --host 0.0.0.0 --port 443 \
    --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
  ```
  `https://localhost` is added to `CORS_ORIGINS` so a browser page loaded over
  HTTPS can call this endpoint; the plaintext origins are kept for the `:80`
  frontend.
- **Host access:** `https://localhost/api/v1/docs` and
  `https://localhost/api/v1/health` from the Mac (accept the self-signed cert).
- **Teardown:** kill the `:443` listener by PID (from `ss -ltnp`), delete
  `backend/certs/`. Fully reversible; the `:8000` instance and the dev DB are
  untouched.

## Non-goals

- **No production TLS.** Production terminates TLS at a real reverse proxy / LB
  with a CA-issued cert; this doc is strictly the local devcontainer.
- **No change to the frontend's API base.** The `:80` frontend keeps calling
  `http://localhost:8000`. Pointing it at the HTTPS backend is a separate change.
- **No `docker compose`** — incompatible with this devcontainer (DinD on
  aarch64/linuxkit); everything stays native.
- **Secrets:** the dev key/cert are never committed (`backend/.gitignore`
  ignores `certs/`).
