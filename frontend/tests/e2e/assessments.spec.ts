import { expect, test } from "@playwright/test";

/**
 * F3 — assessment slice (architecture.md §3 `(app)/assessments/*`, FR-10..15).
 *
 * The assessment instrument list, runner, and the sensitive result view all live
 * in the authenticated `(app)` route group, behind the client-side session guard
 * (`(app)/layout.tsx`) and the consent gate (CP-1). These specs assert the
 * **guard contract** that holds WITHOUT any seeded credentials: an anonymous
 * visitor to any assessment route is redirected to `/login` and never sees the
 * protected UI (CP-7 dead-end avoidance; sensitive surfaces are never exposed
 * to an unauthenticated client).
 *
 * SEED GAP (authenticated happy-path): exercising the full
 * list → run → submit → result(view/export/delete) flow needs a seeded student
 * account (with active guardian consent for an under-16 learner) plus a login
 * helper. `docker-compose.test.yml` currently seeds only a published career +
 * content item for the F2 public pages — there is NO seeded authenticated user
 * and no E2E auth/login fixture. Those scenarios are intentionally NOT stubbed
 * here; once a seeded learner + login storage-state fixture exists, add the
 * authenticated happy-path spec.
 */

const ASSESSMENT_ROUTES = [
  "/assessments",
  "/assessments/riasec",
  "/assessments/results/some-result-id",
];

test.describe("assessment routes are guarded (anonymous)", () => {
  for (const route of ASSESSMENT_ROUTES) {
    test(`redirects an anonymous visitor from ${route} to /login`, async ({
      page,
    }) => {
      await page.goto(route);

      // The (app) guard resolves the session to anonymous and replaces to
      // /login; the protected assessment UI is never shown.
      await page.waitForURL(/\/login(\?.*)?$/);
      await expect(
        page.getByRole("heading", { level: 3, name: "Đăng nhập" }),
      ).toBeVisible();
    });
  }
});
