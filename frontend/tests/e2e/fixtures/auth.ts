import { randomUUID } from "node:crypto";
import { readFileSync } from "node:fs";

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
 *
 * Post-N-3 (email-verification-2026-06.md): register no longer opens a session.
 * A fresh account must register → read the mailed link out of the FileMailer
 * outbox → hit /verify-email → then log in. `registerAdult`/`registerChild`
 * fold that whole chain together so downstream specs still get a logged-in
 * session on the expected landing page.
 */

/** Default password satisfying the register schema (≥8, upper+lower+digit). */
export const TEST_PASSWORD = "WeUpPass123";

/**
 * Budget for a post-action navigation/visibility assertion. The register→verify
 * →login chain makes several proxied round-trips before each client redirect; on
 * the slower Firefox/WebKit engines on the aarch64 CI box those exceed
 * Playwright's implicit 5s assertion timeout although they finish well under
 * this. Behaviour is identical across engines — only the timing differs.
 */
const NAV_TIMEOUT = 15_000;

/**
 * FileMailer outbox the native harness points the backend at (the harness sets
 * WEUP_MAILER_OUTBOX before booting uvicorn). Each line is one NDJSON record
 * `{ to, verify_url, ... }` appended whenever /auth/register or
 * /auth/resend-verification "sends" a verification email.
 */
const OUTBOX_PATH = process.env.WEUP_MAILER_OUTBOX ?? "/tmp/weup-outbox.ndjson";

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
 * Read the verification token most recently mailed to `email` out of the
 * FileMailer outbox. The token never reaches the browser (email-only delivery),
 * so the e2e flow recovers it the way a real inbox would. Scans newest-first and
 * throws a clear error if no message for `email` exists — that fails the test at
 * the real cause instead of as a later opaque verify-invalid assertion.
 */
export function readVerifyToken(email: string): string {
  const lines = readFileSync(OUTBOX_PATH, "utf8")
    .split("\n")
    .filter((line) => line.trim() !== "");
  // Newest-first: the latest mail for an email wins (covers resend).
  for (const line of [...lines].reverse()) {
    const rec = JSON.parse(line) as { to?: string; verify_url?: string };
    if (rec.to === email && rec.verify_url) {
      const token = new URL(rec.verify_url).searchParams.get("token");
      if (token) return token;
    }
  }
  throw new Error(`No verification email for ${email} in ${OUTBOX_PATH}`);
}

/**
 * Poll the outbox for the verification token. The backend appends the line
 * during the register POST, which resolves before the check-email notice
 * renders — but the file write can lag the response by a beat, so retry briefly
 * instead of reading once and racing the flush.
 */
async function waitForVerifyToken(email: string): Promise<string> {
  let token = "";
  await expect(() => {
    token = readVerifyToken(email);
  }).toPass({ timeout: 10_000 });
  return token;
}

/** The post-register notice heading (CheckEmailNotice / vi.json checkEmailTitle). */
const CHECK_EMAIL_HEADING = "Kiểm tra hộp thư của bạn";
/** The verify-success heading (VerifyEmailView / vi.json verifySuccessTitle). */
const VERIFY_SUCCESS_HEADING = "Email đã được xác minh";

/**
 * Submit an already-filled register form and assert the deterministic
 * check-your-email notice (no session, no redirect — N-3). Returns the creds so
 * a caller can verify and/or log in afterwards. Use this directly when a test
 * needs the *unverified* state (resend, login-before-verify-403).
 */
export async function submitRegister(
  page: Page,
  fields: RegisterFields,
): Promise<Credentials> {
  await fillRegisterForm(page, fields);
  await clickRegister(page);
  await expect(
    page.getByRole("heading", { name: CHECK_EMAIL_HEADING }),
  ).toBeVisible({ timeout: NAV_TIMEOUT });
  return { email: fields.email, password: fields.password };
}

/**
 * From the check-email notice, recover the mailed token and complete
 * verification by navigating to /verify-email?token=…, asserting the success
 * view. Leaves the page on the verify-success screen (no session yet).
 */
export async function verifyEmailViaLink(page: Page, email: string) {
  const token = await waitForVerifyToken(email);
  await page.goto(`/verify-email?token=${encodeURIComponent(token)}`);
  await expect(
    page.getByRole("heading", { name: VERIFY_SUCCESS_HEADING }),
  ).toBeVisible({ timeout: NAV_TIMEOUT });
}

/** Register a fresh account and carry it through email verification. */
async function registerAndVerify(
  page: Page,
  fields: RegisterFields,
): Promise<Credentials> {
  const creds = await submitRegister(page, fields);
  await verifyEmailViaLink(page, fields.email);
  return creds;
}

/**
 * Register a fresh ADULT (working, born 1995 → `active`), verify the email, and
 * log in — landing on the dashboard. Returns the credentials for reuse.
 */
export async function registerAdult(
  page: Page,
  email = uniqueEmail(),
): Promise<Credentials> {
  const creds = await registerAndVerify(page, {
    email,
    dob: "1995-01-01",
    userType: "working",
    schoolLevel: "none",
    password: TEST_PASSWORD,
  });
  await loginAs(page, creds);
  return creds;
}

/**
 * Register a fresh UNDER-16 student (born 2013 → `pending_guardian_consent`),
 * verify the email, and log in — landing on the guardian-consent screen (CP-1).
 * The pending→/consent routing now runs at login (only a verified session can
 * reach it), not at register. Returns the credentials.
 */
export async function registerChild(
  page: Page,
  email = uniqueEmail("f-child"),
  dob = "2013-09-01",
): Promise<Credentials> {
  const creds = await registerAndVerify(page, {
    email,
    dob,
    userType: "student",
    schoolLevel: "lower_secondary",
    password: TEST_PASSWORD,
  });
  await loginAs(page, creds, /\/consent$/);
  return creds;
}

/**
 * Log in through the UI on the current page and assert the landing URL. Defaults
 * to /dashboard; pass `expectUrl` for status-routed accounts (e.g. /consent for
 * a verified under-16 in `pending_guardian_consent`).
 */
export async function loginAs(
  page: Page,
  { email, password }: Credentials,
  expectUrl: RegExp = /\/dashboard$/,
) {
  await page.goto("/login");
  await fillAndConfirm(page.getByLabel("Email", { exact: true }), email);
  await fillAndConfirm(page.getByLabel("Mật khẩu", { exact: true }), password);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await expect(page).toHaveURL(expectUrl, { timeout: NAV_TIMEOUT });
}
