import { expect, test } from "@playwright/test";

import { registerAdult } from "./fixtures/auth";

/**
 * F7 — counselor console (architecture.md §3, §4.4, §7, §10; FR-80..83,
 * CP-3/CP-4).
 *
 * SEED/STACK NOTE: the E2E stack (`docker-compose.test.yml` +
 * `backend/docker-entrypoint.sh`) seeds assessments/competency/careers, a demo
 * school and wellbeing content, but intentionally NO users and NO school
 * memberships — counselor/student enrollment is left to runtime, and public
 * registration cannot grant the `counselor` role. So there is no way to
 * self-register a real counselor through the public UI, and the POSITIVE
 * counselor views (de-sensitized roster + student view + session form) are
 * covered by the vitest component tests
 * (`desensitized-student-view.test.tsx`, `roster-table.test.tsx`,
 * `session-form.test.tsx`, `counselor-students-page.test.tsx`) rather than
 * end-to-end. If a seeded counselor + assigned students fixture is added later,
 * a positive-path E2E can be appended.
 *
 * What IS exercised end-to-end here: the role gate (CP-4). A freshly registered
 * ADULT (no `counselor` role) is blocked from `/counselor/students` and sees the
 * neutral "no access" state — no roster, no info leak about what exists.
 */

test.describe("counselor console — role gate (non-counselor)", () => {
  test("blocks an adult without the counselor role from the roster (CP-4)", async ({
    page,
  }) => {
    await registerAdult(page);
    await page.goto("/counselor/students");

    // The role gate shows the neutral no-access block.
    await expect(page.getByText("Bạn không có quyền truy cập")).toBeVisible();

    // No roster is rendered, and the page does not redirect-loop away.
    await expect(page).toHaveURL(/\/counselor\/students$/);
    await expect(
      page.getByRole("heading", { name: "Học sinh được phân công" }),
    ).toBeHidden();
  });
});
