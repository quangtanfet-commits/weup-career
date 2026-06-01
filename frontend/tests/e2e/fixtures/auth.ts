import { randomUUID } from "node:crypto";

import { expect, type Locator, type Page } from "@playwright/test";

/**
 * Shared auth helpers for the e2e suite. Extracted from the per-spec copies that
 * had drifted across counselor/wellbeing/admin-editor/recommendations specs so
 * the registration + login flows are described in exactly one place.
 *
 * These drive the REAL UI (register/login forms) against the native prod build
 * on :3100 with the same-origin /api proxy (see scripts/run-validation-native.sh
 * and next.config.ts). They cover only UI-observable behaviour; API/DB-level
 * invariants (token hashing, rotation, expiry, audit rows) are owned by the
 * backend pytest suite.
 */

/** Default password satisfying the register schema (≥8, upper+lower+digit). */
export const TEST_PASSWORD = "WeUpPass123";

/**
 * Budget for a post-submit redirect assertion. Register does two proxied
 * round-trips (register → login) before the client redirect; on the slower
 * Firefox/WebKit engines on the aarch64 CI box that chain exceeds Playwright's
 * implicit 5s assertion timeout although it finishes well under this. Behaviour
 * is identical across engines — only the timing differs.
 */
const NAV_TIMEOUT = 15_000;

export type Credentials = { email: string; password: string };

export function uniqueEmail(prefix = "f-auth"): string {
  const rand = randomUUID().slice(0, 8);
  return `${prefix}-${Date.now()}-${rand}@example.vn`;
}

/**
 * Fill a react-hook-form field so the value reliably sticks.
 *
 * On WebKit the first `fill()` can land before Next.js finishes hydrating the
 * controlled input; hydration then resets it to its default ("") and the typed
 * value is silently lost. Re-filling until the value holds makes the helper
 * deterministic across Chromium/Firefox/WebKit instead of racing hydration.
 */
export async function fillAndConfirm(field: Locator, value: string) {
  await expect(async () => {
    await field.fill(value);
    await expect(field).toHaveValue(value, { timeout: 1000 });
  }).toPass({ timeout: 10_000 });
}

type RegisterFields = {
  email: string;
  dob: string;
  userType: "working" | "student";
  schoolLevel:
    | "primary"
    | "lower_secondary"
    | "upper_secondary"
    | "tertiary"
    | "none";
  password: string;
};

/** Navigate to /register and fill every field. Does NOT submit. */
export async function fillRegisterForm(page: Page, fields: RegisterFields) {
  await page.goto("/register");
  await fillAndConfirm(page.getByLabel("Email", { exact: true }), fields.email);
  await fillAndConfirm(
    page.getByLabel("Ngày sinh", { exact: true }),
    fields.dob,
  );
  await page.getByLabel("Bạn là").selectOption({ value: fields.userType });
  await page.getByLabel("Cấp học").selectOption({ value: fields.schoolLevel });
  // "Mật khẩu" is a prefix of the confirm label, so match it exactly.
  await fillAndConfirm(
    page.getByLabel("Mật khẩu", { exact: true }),
    fields.password,
  );
  await fillAndConfirm(
    page.getByLabel("Xác nhận mật khẩu", { exact: true }),
    fields.password,
  );
}

function clickRegister(page: Page) {
  return page.getByRole("button", { name: "Đăng ký", exact: true }).click();
}

/**
 * Register a fresh ADULT (working, born 1995 → `active`) through the UI and land
 * on the dashboard. Returns the credentials so a later login can reuse them.
 */
export async function registerAdult(
  page: Page,
  email = uniqueEmail(),
): Promise<Credentials> {
  await fillRegisterForm(page, {
    email,
    dob: "1995-01-01",
    userType: "working",
    schoolLevel: "none",
    password: TEST_PASSWORD,
  });
  await clickRegister(page);
  await expect(page).toHaveURL(/\/dashboard$/, { timeout: NAV_TIMEOUT });
  return { email, password: TEST_PASSWORD };
}

/**
 * Register a fresh UNDER-16 student (born 2013 → `pending_guardian_consent`)
 * through the UI and land on the guardian-consent screen (CP-1). Returns creds.
 */
export async function registerChild(
  page: Page,
  email = uniqueEmail("f-child"),
  dob = "2013-09-01",
): Promise<Credentials> {
  await fillRegisterForm(page, {
    email,
    dob,
    userType: "student",
    schoolLevel: "lower_secondary",
    password: TEST_PASSWORD,
  });
  await clickRegister(page);
  await expect(page).toHaveURL(/\/consent$/, { timeout: NAV_TIMEOUT });
  return { email, password: TEST_PASSWORD };
}

/** Log in through the UI on a fresh (anonymous) page and land on the dashboard. */
export async function loginAs(page: Page, { email, password }: Credentials) {
  await page.goto("/login");
  await fillAndConfirm(page.getByLabel("Email", { exact: true }), email);
  await fillAndConfirm(page.getByLabel("Mật khẩu", { exact: true }), password);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard$/, { timeout: NAV_TIMEOUT });
}
