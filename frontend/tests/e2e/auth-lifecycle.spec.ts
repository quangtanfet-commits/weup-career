import { expect, test } from "@playwright/test";

import {
  fillAndConfirm,
  fillRegisterForm,
  loginAs,
  registerAdult,
  registerChild,
  submitRegister,
  TEST_PASSWORD,
  uniqueEmail,
  verifyEmailViaLink,
} from "./fixtures/auth";

/**
 * Auth lifecycle E2E (spec.md §3.1 FR-01/02/05/06; CP-1, CP-7; email-
 * verification-2026-06.md). Holdout scenarios: registration-age-gate.feature,
 * auth-session.feature.
 *
 * SCOPE — UI-observable only. The honest test set has many API/DB-level
 * assertions (202 AcceptedResponse body, SHA-256 token hashing, single-use
 * consumption, 24h expiry, refresh rotation revoked_at, 15-min access expiry,
 * email lowercasing, weak-password 422). Those are NOT browser-observable and
 * are pinned 1:1 by backend pytest (tests/integration/test_auth_api.py,
 * test_email_verification.py, test_guardian_api.py). Re-asserting them through
 * Playwright would be slower and weaker, so this file covers only what a user
 * actually sees: the register→verify→login flow, the age-gate routing, surfaced
 * error states (generic 401, not-verified 403), and the protected-route guard.
 * There is intentionally no logout test — the product exposes no logout control
 * in the UI yet.
 *
 * N-3: register no longer opens a session. The fixtures recover the mailed
 * verification link from the FileMailer outbox (the harness sets
 * WEUP_MAILER_OUTBOX), so `registerAdult`/`registerChild` fold register→verify
 * →login into one call and still land on the expected page.
 */

test.describe("registration age gate (CP-1)", () => {
  test("an adult (≥16) registers, verifies, and lands on the dashboard", async ({
    page,
  }) => {
    await registerAdult(page);
    // registerAdult already asserts /dashboard after verify+login; restate it.
    await expect(page).toHaveURL(/\/dashboard$/);
  });

  test("an under-16 registrant lands on the guardian-consent screen", async ({
    page,
  }) => {
    // pending_guardian_consent → /consent routing now runs at login (only a
    // verified session can reach it); registerChild verifies then logs in.
    await registerChild(page);
    await expect(page).toHaveURL(/\/consent$/);
    // Real consent copy (NOT the scenario's paraphrase "Cần người thân đồng ý").
    await expect(
      page.getByRole("heading", { name: "Đồng ý của người giám hộ" }),
    ).toBeVisible();
  });
});

test.describe("email verification (N-3)", () => {
  test("register shows the deterministic check-your-email notice (no session)", async ({
    page,
  }) => {
    // submitRegister asserts the check-email heading and does NOT navigate into
    // the app — there is no pre-verification session.
    await submitRegister(page, {
      email: uniqueEmail("f-notice"),
      dob: "1995-01-01",
      userType: "working",
      schoolLevel: "none",
      password: TEST_PASSWORD,
    });
    await expect(page).toHaveURL(/\/register$/);
  });

  test("following the mailed link verifies the account", async ({ page }) => {
    const email = uniqueEmail("f-verify");
    await submitRegister(page, {
      email,
      dob: "1995-01-01",
      userType: "working",
      schoolLevel: "none",
      password: TEST_PASSWORD,
    });
    // verifyEmailViaLink reads the token from the outbox, hits /verify-email,
    // and asserts the success view.
    await verifyEmailViaLink(page, email);
  });

  test("an invalid token shows the generic invalid state (no enumeration)", async ({
    page,
  }) => {
    await page.goto("/verify-email?token=not-a-real-token");
    await expect(
      page.getByRole("heading", {
        name: "Liên kết không hợp lệ hoặc đã hết hạn",
      }),
    ).toBeVisible();
    // Assert the specific invalid-state copy, not a bare role=alert: Next's empty
    // __next-route-announcer__ also carries role=alert and trips strict mode (same
    // collision handled in the login tests below).
    await expect(
      page.getByText(
        "Liên kết xác minh không còn hiệu lực. Hãy yêu cầu gửi lại một liên kết mới.",
      ),
    ).toBeVisible();
  });

  test("resending from the check-email notice surfaces the neutral confirmation", async ({
    page,
  }) => {
    await submitRegister(page, {
      email: uniqueEmail("f-resend"),
      dob: "1995-01-01",
      userType: "working",
      schoolLevel: "none",
      password: TEST_PASSWORD,
    });
    await page.getByRole("button", { name: "Gửi lại email xác minh" }).click();
    await expect(
      page.getByText(
        "Nếu thông tin hợp lệ, chúng tôi đã gửi lại email xác minh.",
      ),
    ).toBeVisible();
  });
});

test.describe("login (CP-7)", () => {
  test("valid credentials on a fresh session land on the dashboard", async ({
    page,
    browser,
  }) => {
    // Create + verify the account in this context (registerAdult also logs in)…
    const creds = await registerAdult(page);

    // …then log in from a clean, anonymous context (no refresh cookie, no
    // in-memory token) to exercise the real login form end-to-end.
    const ctx = await browser.newContext();
    const fresh = await ctx.newPage();
    await loginAs(fresh, creds);
    await expect(fresh).toHaveURL(/\/dashboard$/);
    await ctx.close();
  });

  test("logging in before verifying shows the not-verified notice with a resend (403)", async ({
    page,
    browser,
  }) => {
    // Register but do NOT verify — the account is unverified.
    const creds = await submitRegister(page, {
      email: uniqueEmail("f-unverified"),
      dob: "1995-01-01",
      userType: "working",
      schoolLevel: "none",
      password: TEST_PASSWORD,
    });

    // A correct password on the unverified account returns 403
    // EMAIL_NOT_VERIFIED — a distinct message (not the generic 401) plus a
    // resend affordance, and no navigation into the app.
    const ctx = await browser.newContext();
    const fresh = await ctx.newPage();
    await fresh.goto("/login");
    await fillAndConfirm(
      fresh.getByLabel("Email", { exact: true }),
      creds.email,
    );
    await fillAndConfirm(
      fresh.getByLabel("Mật khẩu", { exact: true }),
      creds.password,
    );
    await fresh.getByRole("button", { name: "Đăng nhập", exact: true }).click();

    await expect(
      fresh.getByText(
        "Tài khoản chưa được xác minh email. Vui lòng kiểm tra hộp thư hoặc gửi lại liên kết.",
      ),
    ).toBeVisible();
    await expect(fresh).toHaveURL(/\/login$/);

    // The resend affordance works and confirms neutrally.
    await fresh.getByRole("button", { name: "Gửi lại email xác minh" }).click();
    await expect(
      fresh.getByText(
        "Nếu thông tin hợp lệ, chúng tôi đã gửi lại email xác minh.",
      ),
    ).toBeVisible();
    await ctx.close();
  });

  test("a wrong password shows a generic error and stays on /login", async ({
    page,
    browser,
  }) => {
    const creds = await registerAdult(page);

    const ctx = await browser.newContext();
    const fresh = await ctx.newPage();
    await fresh.goto("/login");
    await fillAndConfirm(
      fresh.getByLabel("Email", { exact: true }),
      creds.email,
    );
    await fillAndConfirm(
      fresh.getByLabel("Mật khẩu", { exact: true }),
      "WrongPass999",
    );
    await fresh.getByRole("button", { name: "Đăng nhập", exact: true }).click();

    // Generic credential error is surfaced (anti-enumeration) and the user is
    // not navigated into the app. Assert the specific message rather than a bare
    // role=alert: WebKit also exposes Next's empty __next-route-announcer__ with
    // role=alert, which trips strict mode.
    await expect(
      fresh.getByText("Email hoặc mật khẩu không đúng"),
    ).toBeVisible();
    await expect(fresh).toHaveURL(/\/login$/);
    await ctx.close();
  });
});

test.describe("registration edge cases", () => {
  test("re-registering an existing email is indistinguishable from a fresh signup (H-04: no email-exists oracle)", async ({
    page,
    browser,
  }) => {
    // Create + verify an account once (adult).
    const creds = await registerAdult(page);

    // Re-submit register with the SAME email from a clean context. Post-N-3 the
    // endpoint always answers 202 AcceptedResponse regardless of whether the
    // email exists, so RegisterForm shows the SAME check-your-email notice as a
    // brand-new signup — there is no "email already registered" oracle and no
    // session is opened. (See docs/security/email-enumeration.md §4.6 +
    // email-verification-2026-06.md §3.1. DB-level no-op / no password-overwrite
    // invariants are pinned by backend pytest.)
    const ctx = await browser.newContext();
    const fresh = await ctx.newPage();
    await submitRegister(fresh, {
      email: creds.email,
      dob: "1995-01-01",
      userType: "working",
      schoolLevel: "none",
      password: TEST_PASSWORD,
    });
    // Same neutral notice as a fresh signup; the removed oracle must NOT reappear.
    await expect(fresh.getByText("Email đã được đăng ký")).toHaveCount(0);
    await expect(fresh).toHaveURL(/\/register$/);
    await ctx.close();
  });

  test("a weak password is blocked client-side before any redirect", async ({
    page,
  }) => {
    // Pure client Zod validation (schema mirrors the backend ≥8 upper/lower/digit
    // rule). The form never navigates; the field-level error is shown.
    await fillRegisterForm(page, {
      email: uniqueEmail("f-weak"),
      dob: "1995-01-01",
      userType: "working",
      schoolLevel: "none",
      password: "123",
    });
    await page.getByRole("button", { name: "Đăng ký", exact: true }).click();

    await expect(
      page.getByText("Mật khẩu phải có ít nhất 8 ký tự"),
    ).toBeVisible();
    await expect(page).toHaveURL(/\/register$/);
  });
});

test.describe("protected-route guard (CP-7 dead-end avoidance)", () => {
  test("an anonymous visit to a protected route redirects to /login", async ({
    page,
  }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login$/);
  });
});
