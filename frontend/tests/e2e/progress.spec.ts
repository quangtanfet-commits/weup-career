import { expect, test } from "@playwright/test";

/**
 * F4 — K-A-R competency progress slice (architecture.md §11; FR-20..24, CP-8).
 *
 * Unlike the F2 public slices, `/progress` lives in the authenticated `(app)`
 * route group: it reads the learner's personal progress with a bearer token and
 * is consent-gated for children <16 (CP-1/CP-2). So these specs need a *logged-in
 * session* and a *seeded learner with progress* — neither of which the local
 * Playwright server (frontend only, no backend) provides.
 *
 * They are therefore gated behind `E2E_AUTH_READY`. In CI, once the seed grows
 * a known learner (email/password) with at least one recorded indicator and the
 * login helper lands a session, set `E2E_AUTH_READY=1` (and the credential env
 * vars below) to activate them. Until then the suite is skipped — NOT stubbed —
 * so we never assert against a fake backend.
 *
 * Reported gaps for the lead (do not silently work around):
 *  1. Backend seed must publish a learner account with progress rows
 *     (competency, depth_achieved) and a dev_phase per area.
 *  2. A reusable login step (or storageState) is needed to authenticate the
 *     browser context before visiting `/progress`.
 *  3. No nav link to `/progress` exists in the public header yet; the authed
 *     `(app)` shell has no menu in F1/F4. Either add a link in a later slice or
 *     navigate directly to `/progress` once authenticated.
 */

const AUTH_READY = process.env.E2E_AUTH_READY === "1";
const EMAIL = process.env.E2E_LEARNER_EMAIL ?? "";
const PASSWORD = process.env.E2E_LEARNER_PASSWORD ?? "";

test.describe("K-A-R progress (authenticated learner)", () => {
  test.skip(
    !AUTH_READY,
    "Needs a seeded learner + login (set E2E_AUTH_READY=1, E2E_LEARNER_EMAIL/PASSWORD).",
  );

  test.beforeEach(async ({ page }) => {
    // Log in via the real form so a session token is in memory before /progress.
    await page.goto("/login");
    await page.getByLabel("Email").fill(EMAIL);
    await page.getByLabel(/Mật khẩu/).fill(PASSWORD);
    await page.getByRole("button", { name: "Đăng nhập" }).click();
    await expect(page).not.toHaveURL(/\/login$/);
  });

  test("renders the progress overview, dev-phase and competency tree", async ({
    page,
  }) => {
    await page.goto("/progress");

    await expect(
      page.getByRole("heading", { level: 1, name: "Tiến bộ năng lực" }),
    ).toBeVisible();

    // The three K-A-R sections (section titles are <h3> via CardTitle).
    await expect(
      page.getByRole("heading", { name: "Tổng quan tiến bộ K-A-R" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Giai đoạn phát triển nghề nghiệp" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Cây năng lực" }),
    ).toBeVisible();
  });

  test("expands a competency to reveal its K→A→R indicators", async ({
    page,
  }) => {
    await page.goto("/progress");

    const firstCompetency = page.locator("details").first();
    await expect(firstCompetency).toBeVisible();
    await firstCompetency.locator("summary").click();
    await expect(firstCompetency).toHaveJSProperty("open", true);
  });

  test("shows NO depth-downgrade control (CP-8 monotonicity)", async ({
    page,
  }) => {
    await page.goto("/progress");

    // The progress views are read-only: no select/slider/button to lower depth.
    const overview = page
      .getByRole("heading", { name: "Tổng quan tiến bộ K-A-R" })
      .locator("xpath=ancestor::*[1]/following-sibling::*[1]");
    await expect(overview.getByRole("slider")).toHaveCount(0);
    await expect(overview.getByRole("combobox")).toHaveCount(0);
  });
});
