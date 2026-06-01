# Migration: Vitest 2 → 4 (frontend unit-test runner)

- **Slice**: supersedes Dependabot PR #45 (`vitest 2.1.9 → 4.1.7`).
- **Branch**: `chore/fe-vitest-4`
- **Scope**: frontend unit-test runner only (`vitest run`, `vitest run --coverage`).
  No app/runtime code, no Playwright E2E, no Storybook story changes.

## Why a manual slice (not a plain Dependabot merge)

Dependabot bumped **only** `vitest`. A vitest major upgrade requires the
coverage provider to share the same major, and v4 carries config/behaviour
breaks that the bot cannot apply:

1. `@vitest/coverage-v8` is still pinned `^2.1.8` in the PR → **must** move to
   `^4` or vitest aborts with a version-mismatch error.
2. v4 rewrote the V8 coverage engine to **AST-based remapping** — reported
   line/branch numbers shift. Our CI gate is **90/90/90/90**; the slice must
   re-measure and hold the bar (never lower it — excluded files stay explicit).
3. `vitest.shims.d.ts` carries `/// <reference types="@vitest/browser/providers/playwright" />`.
   v4 folds `@vitest/browser` into `vitest` and moves those provider types. We
   run **jsdom only** (no browser mode), so the reference is dead weight and
   would break `tsc --noEmit` (a CI gate).

## Current state (pre-migration)

- `vitest` `^2.1.8` (installed 2.1.9), `@vitest/coverage-v8` `^2.1.9`.
- `vite` `^8.0.15` at root (hoisted by Storybook 10) — satisfies v4's `vite ≥ 6`.
- Node 22.22.2 in CI (`NODE_VERSION`) — satisfies v4's `Node ≥ 20`.
- 71 unit tests under `frontend/tests/**/*.test.{ts,tsx}`.
- `vitest.config.ts`: standalone (no `workspace`/`projects`), `react()` plugin,
  `@`/`server-only` aliases, jsdom, `globals: true`, explicit coverage
  `include`/`exclude`, thresholds 90×4.
- Tests import `{ describe, it, expect, vi }` explicitly from `vitest` — global
  type resolution does **not** depend on `vitest.shims.d.ts`.

## Breaking changes assessed (v2→v3→v4) and how each maps here

| Change (v-introduced) | Impact here | Action |
|---|---|---|
| `vite ≥ 6`, `Node ≥ 20` (v4) | none — vite 8 + Node 22 already | none |
| coverage V8 → AST remapping; `coverage.all` removed (v4) | numbers shift; explicit `include` retained | re-measure; hold 90×4 |
| `@vitest/browser` folded into `vitest`; provider type paths moved (v4) | `vitest.shims.d.ts` reference goes dead | **delete** `vitest.shims.d.ts` (browser mode unused) |
| `spy.mockReset` restores original impl (v3) | our `.mockReset()` targets are `vi.fn()` mocks, not `vi.spyOn` spies → reset-to-undefined unchanged | verify via full run |
| `vi.restoreAllMocks` restores only `vi.spyOn` spies (v4) | used in `afterEach`; `vi.fn()` mocks are reset by `mockReset`, not `restoreAllMocks` | verify via full run |
| stricter `toEqual`/`toThrowError` error equality (v3) | grep shows no error-shape asserts in unit suite | verify via full run |
| pool option renames, `environmentMatchGlobs`/`poolMatchGlobs`, `deps.inline/external`, `workspace` (v4) | none of these appear in our config | none |
| `invocationCallOrder` 1-based, `getMockName` default (v4) | not used in unit suite (grep clean) | none |

## Plan

1. `package.json`: `vitest ^2.1.8 → ^4.1.7`, `@vitest/coverage-v8 ^2.1.9 → ^4.1.7`.
   Drop the stale root `vite ^8.0.15` pin only if it now conflicts; otherwise leave.
2. Delete `frontend/vitest.shims.d.ts` (dead browser-provider reference).
3. `npm install` to regenerate `package-lock.json`; confirm `@vitest/browser`
   pins disappear or move.
4. Run gates locally and hold every bar:
   - `npx tsc --noEmit`
   - `npm run lint`
   - `npm run format:check`
   - `npm run test` (all 71 green)
   - `npm run test:coverage` (≥ 90/90/90/90; if AST remapping legitimately
     shifts a file below, fix the test or tighten `include`/`exclude` with a
     documented reason — do **not** lower thresholds)
5. Fix any v3/v4 behavioural breaks surfaced by the run (mock semantics) at the
   test level, never by weakening assertions.

## Verification (must all pass before PR)

```
cd frontend
npm ci            # clean install from regenerated lock
npx tsc --noEmit
npm run lint
npm run format:check
npm run test
npm run test:coverage
```

Then push, open PR (cite this doc + supersede #45), merge on green, close #45.

## Out of scope (next slices, sequential — shared package-lock.json)

- **#47 tailwind 4** — CSS-engine rewrite; Chromatic baseline drift risk.
- **#46 next 16** — framework upgrade; largest blast radius; do last.
