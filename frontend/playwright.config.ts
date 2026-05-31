import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config (architecture.md §1, E2E). Browsers are wired here so the
 * lead can author holdout-derived E2E scenarios. The F2 public-content slice
 * adds the first specs under `tests/e2e/`.
 *
 * In CI the full Docker stack (nginx + frontend + backend) is brought up by
 * `docker-compose.test.yml` and the suite talks to nginx on `http://localhost`
 * (env `BASE_URL`). Locally, Playwright boots a single Next.js server on
 * :3000 itself. `E2E_BASE_URL` overrides the base for ad-hoc runs.
 */
const baseURL =
  process.env.E2E_BASE_URL ??
  process.env.BASE_URL ??
  "http://localhost:3000";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  // Per-test budget. The auth specs chain several proxied round-trips
  // (register → login → redirect, sometimes twice across two contexts). In
  // isolation those finish in ~5s, but under `fullyParallel` contention on the
  // constrained aarch64/linuxkit CI box the slower Firefox/WebKit engines can
  // exceed Playwright's 30s default and time out — a harness-capacity artifact,
  // not a product defect (the same test passes deterministically when run
  // alone). 60s gives ~10× headroom over the isolated time while still failing
  // fast on a genuine hang.
  timeout: 60_000,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
  // Only self-host the app for local runs. In CI the Docker stack is already
  // up (and serves via nginx :80), so starting `npm run start` here would be
  // both redundant and bound to the wrong port.
  ...(process.env.CI
    ? {}
    : {
        webServer: {
          command: "npm run start",
          url: "http://localhost:3000",
          reuseExistingServer: true,
          timeout: 120_000,
        },
      }),
});
