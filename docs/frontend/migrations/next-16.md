# Migration: Next.js 15 → 16 (+ coupled next-intl 3 → 4)

- **Slice**: supersedes Dependabot PR #46 (`next 15.5.18 → 16.x`).
- **Branch**: `chore/fe-next-16`
- **Scope**: frontend framework bump — the Next.js runtime/build toolchain and
  the next-intl i18n layer it pins. Touches `package.json`, `next.config.ts`,
  `lib/i18n/request.ts`, `app/layout.tsx`, and a one-line CI fold-in. No app
  feature logic, no backend, no TLA+/conformance surface.
- **Sequence**: 3rd and last of three held FE major bumps. #45 vitest 4 ✓
  (PR #52), #47 tailwind 4 ✓ (PR #53). This is #46 — largest blast radius, run
  last as planned.

## Why a manual slice (not a plain Dependabot merge)

Dependabot #46 stalled because the bump is **not** a single-package change:

1. **Coupled next-intl major.** `next-intl@3.26.5` caps its `next` peer at
   `^15` (`^10 … || ^15.0.0`). Next 16 is outside that range, so npm refuses the
   install — this is almost certainly why Dependabot #46 never went green. Only
   the **next-intl 4.x** line declares `next: "… || ^16.0.0"`. So this slice
   **must** bump `next-intl 3.26.5 → ^4` in lockstep with Next 16.
2. **Engine rewrite-adjacent changes.** Next 16 makes **Turbopack the default
   bundler for both `next dev` and `next build`**, removes `next lint`, and
   raises the Node/TS floors. Each needs a deliberate decision (below), not a
   blind version pin.
3. **next-intl 4 has its own breaking changes** (getRequestConfig contract,
   provider prop inheritance, ESM-only). These are small for us but must be
   applied, not assumed.

## Current state (pre-migration)

- `next` `15.5.18`, `eslint-config-next` `15.5.18`.
- `react` / `react-dom` `19.2.6` (already satisfies Next 16's `react: ^19`).
- `next-intl` `^3.26.1` (installed 3.26.5).
- Single locale `vi`, no URL prefix, no next-intl middleware.
- `lint` script already calls `eslint` directly (not `next lint`) — Next 16's
  removal of `next lint` does **not** affect us.
- No `middleware.ts`, no `app/**/route.ts` handlers, no `next/image` usage, no
  `next/server` imports, no babel/webpack config files.
- Storybook runs on `@storybook/nextjs-vite` (its own Vite builder), independent
  of Next's bundler — Turbopack-by-default does not touch the Storybook build.

## Target

| Package | From | To | Reason |
|---|---|---|---|
| `next` | 15.5.18 | **16.2.6** | latest 16.x (security release: fixes Server-Component DoS, middleware/auth bypass, SSRF, XSS, cache poisoning CVEs) |
| `eslint-config-next` | 15.5.18 | **16.2.6** | must track `next` major |
| `next-intl` | ^3.26.1 | **^4.13.0** | only the 4.x line peers `next ^16` |
| `eslint` | ^8.57.1 | **^9.39.4** | `eslint-config-next@16` peers `eslint >=9` and ships flat-config only |

`react` / `react-dom` `19.2.6` and `@types/react(-dom)` `^19` are unchanged —
already compatible.

> **Discovered coupling (ESLint 8 → 9).** `eslint-config-next@16` declares
> `peerDependencies.eslint: ">=9.0.0"` and is published **as flat config only**.
> On ESLint 8 with the legacy `.eslintrc.json`, the next plugin's flat shape
> fails to load (`TypeError: Converting circular structure to JSON`). So this
> slice also bumps ESLint 8 → 9 and converts the config — see § ESLint
> flat-config migration. `eslint-plugin-storybook@10.4.1` peers `eslint >=8`, so
> it is compatible with 9.

## Breaking-changes audit (Next.js 16)

| Change | Applies here? | Action |
|---|---|---|
| **Turbopack default** for `dev` **and** `build`; `build` aborts if a webpack config is detected | Yes (build path) | We have **no** webpack config, so Turbopack builds cleanly. Verify `next build` under Turbopack with the next-intl plugin + `output: "standalone"` + `rewrites()`. Fallback: `next build --webpack` (documented, not preferred). |
| **`next lint` removed**; `next build` no longer lints; `eslint` config key removed | No | `lint` already invokes `eslint` directly; CI runs it as a separate step. No change. |
| **Node 20.9+ / TS 5.1+ minimums** | Confirm | CI `NODE_VERSION="20"` resolves to 20.x ≥ 20.9 ✓; local node v22 ✓; TS `^5.7.2` ✓. |
| **Async request APIs** (`cookies`/`headers`/`params`/`searchParams`) sync access removed | Already compliant | All dynamic `params`/`searchParams` are `Promise`-typed and `await`ed / `use()`d. No `cookies`/`headers`/`draftMode` calls in app code. |
| `middleware` → `proxy` file rename | No | No middleware file. |
| `next/image` default changes (`qualities`, local-image behaviour) | No | `next/image` unused. |
| `revalidateTag` requires a `cacheLife` 2nd arg | No | Not used; caching is per-fetch `next: { revalidate }`. |
| Parallel routes need explicit `default.js` | No | No parallel routes. |
| `AMP` / `serverRuntimeConfig` / `publicRuntimeConfig` removed | No | None used. |
| `experimental.turbopack` → top-level `turbopack` config key | No | No turbopack config block in `next.config.ts`. |
| `next typegen` (PageProps/LayoutProps helpers) | Optional | Not adopting in this slice; current explicit prop types stay. |

**Net**: the app code is already on Next 15's async-API model, so the runtime
blast radius is low. The real work is the toolchain (Turbopack build verify) and
the coupled next-intl 4 changes.

## next-intl 4 migration touch points

| Area | v3 (now) | v4 change | Action |
|---|---|---|---|
| `getRequestConfig` return | returns `{ locale, messages }` | `locale` is **required** to be returned (we already do) | `lib/i18n/request.ts` already returns `locale: defaultLocale` → no behavioural change. Keep single-locale return; optionally adopt `requestLocale`/`hasLocale` later when we add locales. |
| `NextIntlClientProvider` props | explicit `messages={messages}` | provider **inherits** messages/formats from request config by default; `messages` prop becomes optional | `app/layout.tsx`: the explicit `locale`/`messages` props remain valid. Leave as-is for clarity (no `messages={null}` opt-out needed). |
| Module format | dual | **ESM-only** (except `next-intl/plugin`) | We only `import` next-intl (no `require`) and the plugin entry is the CJS-safe one — no change. |
| `AppConfig` typing | global | scoped to the `next-intl` module augmentation | We have no `AppConfig` augmentation today; not introducing one in this slice. |
| ICU `null`/`undefined`/`boolean` args disallowed | lenient | stricter | Our messages take string/number args only — no nullable ICU args. |
| React 17+ / TS 5 minimums | — | satisfied (React 19, TS 5.7) | none |

## ESLint flat-config migration

`eslint-config-next@16` is flat-config-only and peers `eslint >=9`. The legacy
`.eslintrc.json` is replaced by `eslint.config.mjs`:

- `extends: ["next/core-web-vitals", "next/typescript", "plugin:storybook/recommended"]`
  → spread the flat arrays `eslint-config-next/core-web-vitals`,
  `eslint-config-next/typescript`, and `eslint-plugin-storybook`'s
  `configs["flat/recommended"]`.
- `ignorePatterns` → a leading `{ ignores: [...] }` block (`node_modules` is
  ignored by default in flat config; we keep `lib/api/schema.ts`, `.next/**`,
  `storybook-static/**`).
- Custom rules (`no-explicit-any`, `no-unused-vars` with `^_` patterns) carry
  over verbatim in a trailing config object.
- The `lint` script is unchanged (`eslint app components lib features tests
  --max-warnings 0`) — flat config lints the ts/tsx in those dirs via the next
  configs' `files` globs.

### React Compiler rules (new in this config)

`eslint-config-next@16` enables `eslint-plugin-react-hooks` v6, whose
recommended set now includes React-Compiler-aware rules absent from our Next 15
baseline. Two existing sites trip them — both are **library-interaction
patterns, not defects** — so the rules stay enabled globally (strong gate) and
each site carries a single justified inline disable:

| Site | Rule | Why disabled |
|---|---|---|
| `features/auth/RegisterForm.tsx` | `react-hooks/incompatible-library` | react-hook-form's `watch()` returns a non-memoizable function; React Compiler skips memoizing — inherent to the library. |
| `features/wellbeing/SupportRequestList.tsx` | `react-hooks/set-state-in-effect` | client fetch-on-mount/refresh effect; the data-load pattern react-query would replace. |

**Follow-up (out of scope):** migrate the `useEffect`+`useState` client reads to
`@tanstack/react-query` (already a dep), which removes the
`set-state-in-effect` disable.

## CI fold-in (close out #47's temporary line)

Slice #47 added a one-time, branch-scoped Chromatic re-baseline to
`.github/workflows/ci.yml`:

```yaml
autoAcceptChanges: chore/fe-tailwind-4
```

It only matched the now-merged tailwind branch and is dead config. **Remove it
in this slice** (the comment block above it too) so the Chromatic gate is back
to "fail on any unaccepted drift" with no branch exception. See
`docs/frontend/migrations/tailwind-4.md` § Re-baselining Chromatic.

## Risks & rollback

- **Turbopack build differences.** Turbopack is a different bundler; the
  `standalone` output and the next-intl plugin are both Turbopack-supported, but
  the verification step below is the gate. If the Turbopack build misbehaves,
  fall back to `next build --webpack` and file a follow-up — do not ship a
  broken prod build path.
- **Chromatic drift.** A framework bump can shift rendered pixels. Adjudicate
  every Chromatic diff (do **not** blanket-accept); a clean run is expected
  since styling/tokens are unchanged.
- **next-intl runtime regressions.** Covered by the existing i18n unit tests +
  the E2E suite (Vietnamese copy assertions). Rollback = revert the branch; the
  three bumps are independent slices so #46 can revert without touching #45/#47.

## Verification plan (full frontend suite, native)

Run from `frontend/` after `npm install`:

```
npm run typecheck        # tsc --noEmit (TS 5.7, Next 16 types)
npm run lint             # eslint, --max-warnings 0
npm run format:check     # prettier (CI gates this separately)
npm run build            # next build (Turbopack default) — standalone + rewrites + next-intl
npm run build-storybook  # @storybook/nextjs-vite (independent of Next bundler)
npm run test:coverage    # vitest — must hold ≥90% line+branch+func+stmt (baseline 93.25/91.47/93.12/93.13)
npm run e2e              # Playwright ×3 browsers, native harness (E2E_PROXY_API=1, port 3100)
```

All must pass before PR. Then: commit (no AI attribution), open PR, merge on
green via **merge-commit** (not squash), close Dependabot #46.

## Out of scope

- Adopting `next typegen` / `PageProps` helpers — current explicit prop types
  are fine; revisit if/when we add more dynamic routes.
- next-intl `requestLocale`/`hasLocale` multi-locale plumbing — only needed when
  a second locale ships (MVP is `vi`-only).
- `proxy.ts` (renamed middleware) — no middleware exists to rename.
