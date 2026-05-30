# WeUp Career — Frontend

Frontend for **WeUp Career**, the Vietnamese national career-guidance platform
(nền tảng hướng nghiệp quốc gia) for THCS/THPT students.

**Stack:** Next.js 15 (App Router) · React 19 · TypeScript 5 (strict) · Tailwind
CSS + shadcn/ui (Radix) · TanStack Query v5 · Zustand · next-intl (vi).

Binding decisions: [ADR-014](../docs/adr/ADR-014-frontend-framework.md) (framework),
[ADR-004](../docs/adr/ADR-004-state-management.md) (state),
[ADR-006](../docs/adr/ADR-006-docker-strategy.md) (Docker), and the detailed
blueprint in [docs/frontend/architecture.md](../docs/frontend/architecture.md).

## Architecture in one screen

- **`app/(public)/`** — anonymous, SEO-facing routes rendered as **React Server
  Components**. They fetch public career/content reads (`GET /api/v1/careers`,
  `/content`) **with no Authorization header** (BE-1 makes these
  anonymous-readable; published-only is enforced server-side) and use ISR
  (`revalidate`). The demo page is `app/(public)/nghe-nghiep/page.tsx`.
- **`app/(app)/`** — authenticated, client-rendered routes. Personal/sensitive
  data is fetched **client-side only**, never in an RSC, so it cannot leak into
  the server render cache.
- **`app/(auth)/`** — login/register (no token yet).
- **Access token** lives **in memory only** (Zustand store, `lib/auth/store.ts`)
  — never localStorage, never a server cache.
- **Typed API client** — `lib/api/schema.ts` is generated from the backend
  OpenAPI 3.1 schema. Two fetch wrappers: `lib/api/server.ts` (anonymous RSC,
  `BACKEND_INTERNAL_URL`) and `lib/api/client.ts` (authed client, injects the
  in-memory bearer).

```
frontend/
├── app/
│   ├── (public)/            # RSC, anonymous, SEO
│   │   ├── page.tsx                 # marketing home
│   │   └── nghe-nghiep/page.tsx     # career library (anonymous-RSC demo)
│   ├── (app)/               # authenticated, client-rendered shell
│   │   └── dashboard/page.tsx
│   ├── (auth)/login/page.tsx
│   ├── layout.tsx           # root: font, next-intl, providers
│   └── not-found.tsx
├── components/ui/           # Button, Card (shadcn/ui, code-in-repo)
├── features/careers/        # CareerCard
├── lib/
│   ├── api/                 # config, server.ts, client.ts, errors, schema.ts, endpoints/
│   ├── auth/store.ts        # in-memory Zustand auth store
│   ├── i18n/                # next-intl config (vi default)
│   └── query/               # TanStack Query provider + client
├── messages/vi.json         # UI-chrome strings (Vietnamese)
├── styles/globals.css       # design tokens (CSS variables)
├── tests/                   # Vitest + Testing Library
├── e2e/                     # Playwright root (scenarios authored by lead)
└── Dockerfile               # multi-stage, Node standalone runtime
```

## Prerequisites

- Node.js 20+ (CI/Docker pin) — local dev tested on Node 22.
- The backend at `../backend` (for `npm run gen:api`) needs `uv` + Python 3.12,
  **or** point `OPENAPI_URL` at a running backend.

## Setup

```bash
npm install
cp .env.example .env          # adjust BACKEND_INTERNAL_URL / NEXT_PUBLIC_API_BASE_URL
```

## Commands

| Command | What it does |
| --- | --- |
| `npm run dev` | Next.js dev server on `http://localhost:3000`. |
| `npm run build` | Production build (`output: standalone`). |
| `npm run start` | Serve the production build. |
| `npm run typecheck` | `tsc --noEmit` (strict). |
| `npm run lint` | ESLint (`next/core-web-vitals` + TS, no `any`). |
| `npm run test` | Vitest unit/component suite. |
| `npm run test:coverage` | Vitest with V8 coverage (90% thresholds on shipped logic). |
| `npm run gen:api` | Regenerate `lib/api/schema.ts` from the backend OpenAPI. |
| `npm run e2e` | Playwright (no scenario tests in F1). |

## Generating API types (drift gate)

`npm run gen:api` runs the hermetic backend exporter
(`python -m app.openapi_export`, placeholder secrets, no DB) via `uv`, writes
`openapi.json`, then runs `openapi-typescript` into `lib/api/schema.ts`. In CI
this is the drift gate (NFR-20 / BE-2): regenerate, then `git diff` must be
empty. To generate from a running backend instead:

```bash
OPENAPI_URL=http://localhost:8000/api/v1/openapi.json npm run gen:api
```

## Docker

Multi-stage build per ADR-006 (Node-runtime standalone, since RSC public routes
need a Node server; nginx is the reverse proxy in front, not the app server):

```bash
docker build -t weup-frontend .
docker run -p 3000:3000 \
  -e BACKEND_INTERNAL_URL=http://backend:8000 \
  -e NEXT_PUBLIC_API_BASE_URL=https://api.weup.vn \
  weup-frontend
```

The runtime stage runs as a non-root user and copies only
`.next/standalone` + `.next/static` + `public/`. A `HEALTHCHECK` probes `/`.

## Scope

This is the **F1 foundation** slice (scaffold + anonymous-RSC public path). The
feature slices (auth/consent forms, assessments, competency, recommendations,
wellbeing, counselor/admin/editor consoles) are F2–F9 per
[architecture.md §11](../docs/frontend/architecture.md).
