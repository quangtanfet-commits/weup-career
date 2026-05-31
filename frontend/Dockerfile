# syntax=docker/dockerfile:1

# Multi-stage build for the WeUp Career frontend (ADR-006 + ADR-014).
# ADR-014 requires a Node.js runtime for the public RSC routes, so this uses
# Next.js `output: "standalone"` instead of a static nginx image. nginx sits in
# front as a reverse proxy (compose/topology), not as the app server.

# ---- Stage 1: deps + build ---------------------------------------------------
FROM node:20-alpine AS builder
WORKDIR /app

# Install dependencies from the lockfile for reproducible builds. .npmrc carries
# legacy-peer-deps=true — Storybook 10 hoists vite@8 while @vitejs/plugin-react@4
# peers on vite<=7, so npm ci needs it to resolve (matches local + CI installs).
COPY package.json package-lock.json .npmrc ./
RUN npm ci

# Build the standalone server. schema.ts is committed, so no backend is needed
# at image-build time.
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1

# NEXT_PUBLIC_* values are inlined into the client bundle at BUILD time, not read
# at runtime. The browser-facing API base therefore must be fixed here, not via a
# compose `environment:` entry (which the client bundle never sees). Default to
# the conventional dev host; the E2E/prod topology overrides it with the
# same-origin edge so authed browser calls route back through nginx (no CORS).
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL

RUN npm run build

# ---- Stage 2: runtime --------------------------------------------------------
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Non-root user (security hardening, ADR-006).
RUN addgroup --system --gid 1001 nodejs \
  && adduser --system --uid 1001 nextjs

# Drop the base image's bundled npm/npx/corepack CLI. The standalone server
# runs with `node server.js` and never invokes npm at runtime, so npm's
# vendored deps (cross-spawn, glob, minimatch, tar) only widen the attack
# surface — Trivy flags their fixable CVEs against this image even though the
# app's own node_modules are clean. Removing them eliminates that whole class.
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx \
  /usr/local/lib/node_modules/corepack /usr/local/bin/corepack

# Copy only the standalone server output + static assets + public files.
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

# The Next.js standalone server answers 200 at "/"; use it as the health probe.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:3000/').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "server.js"]
