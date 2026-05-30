import { expect, test } from "@playwright/test";

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

function uniqueEmail(): string {
  const rand = Math.random().toString(36).slice(2, 10);
  return `f7-counselor-${Date.now()}-${rand}@example.vn`;
}

/**
 * Fill a react-hook-form field so the value reliably sticks.
 *
 * On WebKit the first `fill()` can land before Next.js finishes hydrating the
 * controlled input; hydration then resets it to its default ("") and the typed
 * value is silently lost. Re-filling until the value holds makes the helper
 * deterministic across Chromium/Firefox/WebKit instead of racing hydration.
 */
async function fillAndConfirm(
  field: import("@playwright/test").Locator,
  value: string,
) {
  await expect(async () => {
    await field.fill(value);
    await expect(field).toHaveValue(value, { timeout: 1000 });
  }).toPass({ timeout: 10_000 });
}

/** Register a fresh adult (working) account through the UI and land in the app. */
async function registerAdult(page: import("@playwright/test").Page) {
  await page.goto("/register");

  await fillAndConfirm(
    page.getByLabel("Email", { exact: true }),
    uniqueEmail(),
  );
  // Adult: born well over 16 years ago so the account is `active`, not gated.
  await fillAndConfirm(
    page.getByLabel("Ngày sinh", { exact: true }),
    "1995-01-01",
  );
  await page.getByLabel("Bạn là").selectOption({ value: "working" });
  await page.getByLabel("Cấp học").selectOption({ value: "none" });
  // "Mật khẩu" is a prefix of the confirm label, so match it exactly.
  await fillAndConfirm(
    page.getByLabel("Mật khẩu", { exact: true }),
    "WeUpPass123",
  );
  await fillAndConfirm(
    page.getByLabel("Xác nhận mật khẩu", { exact: true }),
    "WeUpPass123",
  );

  await page.getByRole("button", { name: "Đăng ký", exact: true }).click();

  // Adults are routed to the dashboard (not /consent).
  await expect(page).toHaveURL(/\/dashboard$/);
}

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
