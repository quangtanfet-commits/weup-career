# Visual regression — Storybook + Chromatic

Gap 5 of the full-stack validation checklist: every reusable UI primitive has
Storybook stories covering all visual states, and Chromatic pixel-diffs each
story on every PR so unintended visual drift fails the gate.

## What is in the repo

- **Stories** colocated next to the primitives, `components/ui/*.stories.tsx`:
  `button`, `card`, `input`, `select`, `textarea`, `label`. Each covers the
  states the design tokens distinguish (default / placeholder / disabled /
  `aria-invalid` for inputs; every variant × size for buttons). Plus the curated
  set under `stories/**`.
- **Config** in `frontend/.storybook/` — framework `@storybook/nextjs-vite`
  (Vite builder, deterministic headless `build-storybook`, no webpack dev
  server). `preview.tsx` imports `@/styles/globals.css` so stories render with
  the production Tailwind layer + design tokens (Chromatic diffs the real
  surfaces, not bare DOM).
- **A11y** advisory in the Storybook panel (`addon-a11y`, `a11y.test: "todo"`).
  Authoritative WCAG gating stays in the axe-core E2E spec
  (`tests/e2e/a11y.spec.ts`), not here.

Note: the `@storybook/addon-vitest` browser-test integration that
`storybook init` wires into `vitest.config.ts` was intentionally reverted — it
spins up a Playwright browser runner needing system deps absent in this
devcontainer and would destabilise the jsdom unit suite + 90% coverage gate.

## CI wiring (`.github/workflows/ci.yml`, job `storybook`)

1. **`npm run build-storybook` — always runs.** No external service; a broken
   story or a primitive API drift fails the gate. This is the part that works
   today in CI and in the native runner.
2. **Chromatic publish — gated on `CHROMATIC_PROJECT_TOKEN`.** Runs only when
   the secret is present; `exitZeroOnChanges: false` so unapproved visual drift
   fails the PR. Without the token the step is a no-op (not a hard failure), so
   the pipeline is green for contributors who don't have it.

## To activate Chromatic (one-time, repo owner)

1. Sign in at <https://www.chromatic.com> with the GitHub account and link the
   `weup-career` repo → it issues a **project token**.
2. Add it as a repo secret: **Settings → Secrets and variables → Actions → New
   repository secret**, name `CHROMATIC_PROJECT_TOKEN`.
3. The next PR run publishes a baseline; subsequent PRs diff against it. Approve
   intended changes in the Chromatic UI to update the baseline.

`CHROMATIC_PROJECT_TOKEN` is an **external secret** — it is not in the repo and
cannot be provisioned from this devcontainer. Until it is set, visual
regression is dormant but the `build-storybook` gate is live.

## Local

```bash
cd frontend
npm run storybook        # interactive dev on :6006
npm run build-storybook  # headless build → storybook-static/ (gitignored)
```
