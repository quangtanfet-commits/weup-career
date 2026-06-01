# Migration: Tailwind CSS 3 → 4 (frontend styling engine)

- **Slice**: supersedes Dependabot PR #47 (`tailwindcss 3.4.19 → 4.3.0`).
- **Branch**: `chore/fe-tailwind-4`
- **Scope**: frontend styling toolchain only — the CSS build pipeline
  (`next build`, `build-storybook`) and the design-token wiring. No app/runtime
  TS logic, no unit-test harness, no Playwright spec changes (beyond whatever
  visual baselines legitimately shift).
- **Sequence**: 2nd of three held FE major bumps. #45 vitest 4 ✓ merged
  (PR #52). This is #47. #46 next 16 follows (largest blast radius, last).

## Why a manual slice (not a plain Dependabot merge)

Tailwind v4 is a **ground-up engine rewrite** (Oxide + Lightning CSS), not a
version bump. Dependabot bumped only the `tailwindcss` dependency; it cannot
apply the four coupled changes the new engine requires, and merging it alone
would break the CSS build immediately:

1. **PostCSS plugin extracted.** In v4 `tailwindcss` is no longer itself a
   PostCSS plugin — the plugin moved to a separate package
   `@tailwindcss/postcss`. Our `postcss.config.mjs` lists `tailwindcss: {}`,
   which v4 rejects ("it looks like you're trying to use tailwindcss directly
   as a PostCSS plugin"). Build aborts until the config is rewritten.
2. **Vendor-prefixing is built in.** v4 runs Lightning CSS and handles
   prefixing + nesting itself; the separate `autoprefixer` plugin is now
   redundant and can double-process. It should be removed from the PostCSS
   chain.
3. **CSS-first entry.** The `@tailwind base/components/utilities` directives are
   removed in v4; the entry is a single `@import "tailwindcss";`. The JS config
   file is no longer auto-discovered — it must be opted back in with
   `@config` (or the theme ported to CSS `@theme`).
4. **Preflight default changes** shift rendered pixels (see table). Chromatic
   pixel-diffs every story, so this slice **will** surface visual diffs that a
   human must adjudicate — a bot merge would either fail the Chromatic gate or
   silently bank wrong baselines.

## Current state (pre-migration)

- `tailwindcss` `^3.4.17` (installed 3.4.19), `tailwindcss-animate` `^1.0.7`,
  `autoprefixer` `^10.4.20`, `postcss` `^8.4.49`, `tailwind-merge` `^2.6.0`.
- **`postcss.config.mjs`**: `{ plugins: { tailwindcss: {}, autoprefixer: {} } }`.
- **`tailwind.config.ts`**: JS config — `darkMode: ["class",'[data-theme="dark"]']`,
  `content` globs (`app|components|features/**`), `theme.extend` mapping
  `colors / borderRadius (sm,md,lg) / boxShadow (sm,md,lg) / fontFamily.sans`
  onto the CSS variables in `globals.css`, `plugins:[require("tailwindcss-animate")]`.
- **`styles/globals.css`**: `@tailwind base; @tailwind components; @tailwind
  utilities;` then the `:root` design-token block, a `* { border-color:
  hsl(var(--border)); }` reset, `body` base styles, and a reduced-motion block.
- **Single CSS entry**, imported in `app/layout.tsx` and re-imported in
  `.storybook/preview.tsx` so Storybook/Chromatic render the real surfaces.
- **Build paths that consume PostCSS**: Next.js (`next build`, `output:
  standalone`) and `@storybook/nextjs-vite` (`build-storybook`). Both read the
  same `postcss.config.mjs`, so the plugin swap is a **single change point**
  covering production and Chromatic.
- **Utility-usage audit (drift surface) — grepped `app|components|features`:**
  - No bare `ring`, no bare `shadow`, no bare `rounded`. Ring usage is only
    `ring-2`, `ring-offset-2`, `ring-ring` (explicit width / our `--ring`).
  - `shadow-{sm,md,lg}` and `rounded-{sm,md,lg}` resolve to **our** theme keys
    (mapped to `--shadow-*` / `--radius-*`), so v4's default-scale rename
    (`shadow-sm→shadow-xs`, `rounded→rounded-sm`, …) does **not** touch them.
  - No `bg-opacity-*`, `text-opacity-*`, `flex-grow`, `flex-shrink`,
    `overflow-ellipsis`, `decoration-clone` (all renamed/removed in v4).
  - No `@apply` and no `theme()` calls in `styles/`.
  - `outline-none` appears **6×** — v4 changes its meaning (now
    `outline-style:none`; the old "invisible but present" behaviour moved to
    `outline-hidden`). Review these focus styles.

## Breaking changes assessed (v3→v4) and how each maps here

| Change (v4) | Impact here | Action |
|---|---|---|
| `tailwindcss` no longer a PostCSS plugin; use `@tailwindcss/postcss` | build aborts | **swap** plugin in `postcss.config.mjs` |
| autoprefixer redundant (Lightning CSS prefixes) | double-processing risk | **remove** `autoprefixer` from PostCSS + deps |
| `@tailwind` directives removed → `@import "tailwindcss";` | current entry invalid | **rewrite** top of `globals.css` |
| JS config not auto-loaded | theme/tokens/plugins would silently drop | **keep** via `@config "../tailwind.config.ts";` (preserve exact theme; no token port) |
| `content` auto-detection replaces `content` array | with `@config`, our explicit globs are still honoured | keep globs in JS config; no change |
| Preflight: default border color → `currentColor` | our `* { border-color: hsl(var(--border)) }` reset overrides it | none — already insulated; confirm in Chromatic |
| Preflight: buttons `cursor: pointer`→`default` | visual/UX diff on `<button>` | **DECIDED**: keep the v3 pointer feel — added `button:not(:disabled),[role="button"]:not(:disabled){cursor:pointer}` base rule in `globals.css` (preserves the existing affordance + Chromatic baselines; no per-component churn) |
| Preflight: placeholder color → `currentColor` @ 50% | input placeholder shade shifts | review in Chromatic |
| Default ring width 3px→1px, ring color→`currentColor` | we use `ring-2` + `ring-ring` only (explicit) — **not** affected | confirm; no bare `ring` exists |
| `outline-none` semantics change (6 usages) | focus-visible outline behaviour may shift | review; migrate to `outline-hidden` where the intent was "hidden but accessible" |
| `tailwindcss-animate` (v3-era plugin) vs v4 plugin API | `tailwindcss-animate` still ships an `addUtilities` plugin; shadcn moved to `tw-animate-css` for v4 | **verify build** with `tailwindcss-animate` via `@config`; fallback to `tw-animate-css` only if it breaks (note: switching changes animation utility output → extra Chromatic diff) |
| Browser target raised (Safari 16.4+, Chrome 111+, FF 128+) | drops legacy browsers; our CI browsers (Playwright current chromium/firefox/webkit) satisfy it | record; no action |
| `hsl(var(--…))` token pattern | unchanged in v4 | none |

## Plan

1. **Deps** (`package.json`): add `@tailwindcss/postcss ^4.3.0`; bump
   `tailwindcss ^3.4.17 → ^4.3.0`; **remove** `autoprefixer` (and drop it from
   PostCSS). Keep `tailwindcss-animate` for now; keep `postcss` (Next still
   needs a PostCSS host) and `tailwind-merge`.
2. **`postcss.config.mjs`**: `plugins: { "@tailwindcss/postcss": {} }` (drop
   `tailwindcss` and `autoprefixer`).
3. **`styles/globals.css`**: replace the three `@tailwind` lines with
   ```css
   @import "tailwindcss";
   @config "../tailwind.config.ts";
   ```
   Leave the `:root` tokens, the `*` border reset, `body`, and the
   reduced-motion block untouched (they are plain CSS).
4. **`tailwind.config.ts`**: keep as-is (content globs + `theme.extend` +
   `darkMode` + `plugins`). `@config` makes v4 honour it verbatim, so tokens,
   dark-mode strategy, and the animate plugin carry over with zero token port —
   this is the minimal-drift choice.
5. `npm install` to regenerate `package-lock.json`; confirm `@tailwindcss/*`
   resolves and `autoprefixer` is gone.
6. **Build + verify** (below). If `tailwindcss-animate` fails to load under v4,
   switch to `@plugin "tw-animate-css";` in CSS (add dep, drop the JS `plugins`
   entry) and re-run Chromatic, treating animation diffs as expected.
   **OUTCOME**: `tailwindcss-animate@1.0.7` loaded cleanly via `@config` under
   v4 — both `next build` and `build-storybook` compiled green. **No fallback to
   `tw-animate-css` was needed**, so animation utility output is unchanged (no
   extra Chromatic diff from this axis).
7. **Chromatic adjudication** (the gate that matters): run the visual suite,
   **review every diff**. Accept only intended preflight changes (e.g. button
   cursor) or neutralize unintended drift by adding an explicit base rule in
   `globals.css` to preserve the v3 look. **Do not blanket `--auto-accept`**;
   per house rule, baselines are reviewed, not rubber-stamped.

## Verification (must all pass before PR)

```
cd frontend
npm ci                       # clean install from regenerated lock
npx tsc --noEmit             # unaffected, but a CI gate
npm run lint                 # eslint, max-warnings 0
npm run format:check         # prettier (separate gate)
npm run build                # next build — proves the new PostCSS chain compiles
npm run build-storybook      # proves Storybook's vite+postcss path compiles
npm run test                 # unit suite unaffected (no CSS in jsdom assertions)
npm run test:coverage        # 90/90/90/90 held (CSS change is coverage-neutral)
npm run e2e                   # incl. axe-core a11y spec — catches contrast/focus regressions
```

Then Chromatic runs in CI (`📚 Storybook + Chromatic` check). Review diffs;
hold or consciously re-baseline. Open PR (cite this doc + supersede #47), merge
on green **after** Chromatic diffs are adjudicated, close #47.

### Local verification outcome (2026-06-01, branch `chore/fe-tailwind-4`)

All locally-runnable gates green:

- `tsc --noEmit` ✓ · `lint` ✓ (0 warnings) · `format:check` ✓
- `next build` ✓ · `build-storybook` ✓ — new `@tailwindcss/postcss` chain
  compiles on both Next and Storybook paths.
- `test:coverage` ✓ — **93.25% stmts / 91.47% branch / 93.12% func / 93.13%
  lines** (unchanged from the vitest-4 baseline; CSS change is coverage-neutral).
- `e2e` (chromium, incl. the axe-core a11y spec) ✓ — 28 passed, 3 conditional
  skips (progress specs, unrelated). **No axe contrast/focus regression** from
  the preflight changes. (Note: the auth-register specs require the backend run
  with `RATE_LIMIT_ENABLED=false`; the default 5/hour register cap otherwise
  throttles the suite — a harness env requirement, not a product defect.)

**Chromatic is CI-only** (needs `CHROMATIC_PROJECT_TOKEN`) — adjudicated on the
PR, not locally.

### Chromatic adjudication finding (2026-06-01): every text story flips font

The first Chromatic run on PR #53 flagged **29 diffs across all 6 components**
(Button/Card/Input/Label/Select/Textarea) — far beyond the bounded preflight
deltas above. Empirical A/B (`scripts/sb-capture.mjs`, computed-style dump +
screenshots of a v4 static build vs. a v3 build from parent `9f01539`) pinned
the mechanism — it is **not** a Tailwind-utility regression but a **pre-existing
Storybook font-fidelity bug** that the v4 engine merely re-skinned:

| element | v3 baseline `font-family` | v4 `font-family` |
|---|---|---|
| label / card / button / input | **`"Times New Roman"`** (UA serif) | `ui-sans-serif, system-ui, …` |

Chain of causation:

1. `globals.css` defines `--font-sans: var(--font-be-vietnam-pro), Inter,
   system-ui, sans-serif` and `body { font-family: var(--font-sans) }`.
   `--font-be-vietnam-pro` is injected **only** by `next/font` in
   `app/layout.tsx` (`<html className={beVietnamPro.variable}>`).
2. **Storybook never wired `next/font`** (`.storybook/preview.tsx` imports
   `globals.css` only). So `--font-be-vietnam-pro` is undefined and
   `var(--font-be-vietnam-pro)` — *no inner fallback* — collapses to nothing,
   making `--font-sans` evaluate to a **leading-comma** string
   (`, Inter, system-ui, sans-serif`) → an **invalid** `font-family` → the
   `body` rule is dropped and text inherits the `html` preflight font.
3. **v3** `html` preflight font was `theme('fontFamily.sans')` →
   `var(--font-sans)` → *also* invalid (same leading comma) → cascaded to the
   browser UA default = **Times New Roman**. So the v3 Chromatic baselines were
   silently banking serif text for every story.
4. **v4** `html` preflight font is a hardcoded, *valid* sans fallback
   (`--theme(--default-font-family, ui-sans-serif, system-ui, sans-serif, …)`);
   `@config`'s `fontFamily.sans` feeds the `.font-sans` *utility*, **not** the
   `--default-font-family` var the `html` rule reads. So v4 text falls to
   `ui-sans-serif` — which is why all text flipped serif→sans at once.

**Neither font is the brand font.** The v3 baseline is the bug; matching it
would mean re-banking Times New Roman. The correct resolution is to make
Storybook render the **real** production font so the baselines are meaningful.

**Fix (two parts):**

1. **Storybook font fidelity** — `.storybook/preview.tsx`: instantiate
   `Be_Vietnam_Pro` from `next/font/google` identically to `app/layout.tsx` and
   apply its `.variable` class to `document.documentElement`, mirroring
   production's `<html className={beVietnamPro.variable}>`. `@storybook/
   nextjs-vite` (via `vite-plugin-storybook-nextjs`) fetches + **self-hosts**
   Google fonts at build time, so this is deterministic at render (no runtime
   network) and Chromatic-safe.
2. **Production robustness** — `globals.css`: give the var an inner fallback,
   `--font-sans: var(--font-be-vietnam-pro, ui-sans-serif), Inter, system-ui,
   sans-serif`, so the token can **never** evaluate to an invalid leading-comma
   value even if `next/font` injection is ever absent (defence-in-depth; the
   real bug that made Storybook fall to Times). Production rendering is
   unchanged (the var is defined, so `'Be Vietnam Pro', …` resolves first).

After the fix, Storybook stories render **Be Vietnam Pro** (the production
font). The Chromatic diffs vs. the v3 baseline therefore remain — they are the
intended Times→brand-font **correction**, uniform across every text story, and
are adjudicated/accepted as the new correct baselines (not blanket-accepted:
each is the same explained, deliberate font correction).

## Risks & rollback

- **Highest risk = Chromatic baseline drift.** Bounded by the audit above (no
  bare `ring`/`shadow`/`rounded`; border color already overridden). The likely
  real diffs are button cursor + placeholder shade + possibly `outline-none`
  focus rings. All are CSS-base adjustable without touching components.
- **Second risk = `tailwindcss-animate` v4 compat.** Mitigated by the
  `tw-animate-css` fallback; isolated to animation utilities.
- **Rollback** is a single-commit revert (config + globals.css + package.json/
  lock); no data or API surface touched.

## Re-baselining Chromatic (one-time, branch-scoped)

The 29 Times→Be-Vietnam-Pro diffs are the intended correction, so they must be
accepted **once** to become the new baseline. The Chromatic **UI accept** path
did not work here:

- The gate is the GitHub Actions job `📚 Storybook + Chromatic`, not a
  Chromatic check-run. Chromatic only posts a legacy `UI Tests` commit status,
  which stayed `pending` across builds 48–51 — the manual accept never
  registered server-side (most likely a Reviewer-vs-Viewer permission gap on
  the Chromatic project).
- Even when an accept registers, it flips the commit status but does **not**
  re-run the Actions job; and a same-commit job re-run does not reliably
  inherit a prior same-commit build's acceptance. So the UI path could not
  unblock this PR.

**Decision — programmatic re-baseline scoped to this branch.** Add
`autoAcceptChanges: chore/fe-tailwind-4` to the `chromaui/action@v17` step.
When the running branch matches, Chromatic auto-accepts all changes on that
build, turning the gate green. The acceptance propagates to `main` through the
merge commit's ancestry, so `main` stays green after merge (no diff on the next
unrelated PR).

This is a **one-time** re-baseline, not a policy change: `exitZeroOnChanges:
false` is kept, so any *future* unaccepted drift on any other branch still
fails. The scoped line is dead weight once merged and is removed in the
following slice (#46 next 16) — tracked below.

## Out of scope (next slice)

- **#46 next 16** — framework upgrade; largest blast radius; do last (shared
  `package-lock.json`, so sequential after this merges). **Fold in:** remove
  the one-time `autoAcceptChanges: chore/fe-tailwind-4` line from the Chromatic
  step (it is dead once this branch merges; main's baseline is now the brand
  font).
- Porting the JS `theme.extend` into CSS `@theme` (a v4 idiom) — deferred; the
  `@config` bridge keeps this slice minimal and drift-free. Tracked as possible
  future cleanup, not part of the upgrade.
