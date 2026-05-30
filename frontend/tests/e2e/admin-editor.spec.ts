import { expect, test } from "@playwright/test";

/**
 * F8 — school-admin + content-editor slice (architecture.md §3, §10; FR-80,
 * FR-90, CP-4).
 *
 * These cover the CLIENT ROLE GATE on the role-scoped segments. A freshly
 * registered ADULT account holds no privileged school/editor role (registration
 * is public and cannot grant `school_admin` or `content_editor`), so visiting
 * `/school-admin/classes` and `/editor/content` must show the neutral
 * "không có quyền" block — never the management UI, and never a redirect loop
 * (CP-4: no info leak about what the page would contain).
 *
 * SEED/STACK NOTE: `docker-compose.test.yml` + `backend/docker-entrypoint.sh`
 * seed a demo school + class but NO users and NO memberships, and public
 * registration cannot grant `school_admin`/`content_editor`. There is therefore
 * intentionally no seeded privileged account, so the POSITIVE admin/editor
 * views (class list/create, member assign, content list/create/publish) are NOT
 * exercised end-to-end here — they are covered by the vitest component tests
 * (`school-forms.test.tsx`, `content-editor-forms.test.tsx`,
 * `school-endpoint.test.ts`, `content-editor-endpoint.test.ts`,
 * `role-gate.test.tsx`). If a seeded privileged fixture is added later, a
 * positive-path E2E can be appended.
 */

function uniqueEmail(): string {
  const rand = Math.random().toString(36).slice(2, 10);
  return `f8-admin-editor-${Date.now()}-${rand}@example.vn`;
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

test.describe("role gate blocks non-privileged users (CP-4)", () => {
  test("blocks /school-admin/classes for an adult without school_admin", async ({
    page,
  }) => {
    await registerAdult(page);
    await page.goto("/school-admin/classes");

    // Neutral no-access block — never the management UI.
    await expect(page.getByText("Bạn không có quyền truy cập")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Quản lý lớp" }),
    ).toHaveCount(0);
    // No redirect loop: we stayed on the requested URL.
    await expect(page).toHaveURL(/\/school-admin\/classes$/);
  });

  test("blocks /editor/content for an adult without content_editor", async ({
    page,
  }) => {
    await registerAdult(page);
    await page.goto("/editor/content");

    await expect(page.getByText("Bạn không có quyền truy cập")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Quản lý nội dung" }),
    ).toHaveCount(0);
    await expect(page).toHaveURL(/\/editor\/content$/);
  });
});
