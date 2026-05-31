import { expect, test } from "@playwright/test";

import {
  fillAndConfirm,
  fillRegisterForm,
  loginAs,
  registerAdult,
  registerChild,
  TEST_PASSWORD,
  uniqueEmail,
} from "./fixtures/auth";

/**
 * Auth lifecycle E2E (spec.md §3.1 FR-01/02/05/06; CP-1, CP-7). Holdout
 * scenarios: registration-age-gate.feature, auth-session.feature.
 *
 * SCOPE — UI-observable only. The honest test set has many API/DB-level
 * assertions (201/account_status in the body, SHA-256 token hashing, refresh
 * rotation revoked_at, 15-min access expiry, server-side logout revoke,
 * email lowercasing, weak-password 422). Those are NOT browser-observable and
 * are pinned 1:1 by backend pytest (tests/integration/test_auth_api.py,
 * test_guardian_api.py). Re-asserting them through Playwright would be slower
 * and weaker, so this file covers only what a user actually sees: the age-gate
 * routing, the login result, surfaced error states, and the protected-route
 * guard. There is intentionally no logout test — the product exposes no logout
 * control in the UI yet (only an unused `logout()` client + `clearSession()`
 * store action), so there is nothing to drive end-to-end.
 */

test.describe("registration age gate (CP-1)", () => {
  test("an adult (≥16) registers and lands on the dashboard", async ({
    page,
  }) => {
    await registerAdult(page);
    // registerAdult already asserts /dashboard; restate for readability.
    await expect(page).toHaveURL(/\/dashboard$/);
  });

  test("an under-16 registrant lands on the guardian-consent screen", async ({
    page,
  }) => {
    await registerChild(page);
    await expect(page).toHaveURL(/\/consent$/);
    // Real consent copy (NOT the scenario's paraphrase "Cần người thân đồng ý").
    await expect(
      page.getByRole("heading", { name: "Đồng ý của người giám hộ" }),
    ).toBeVisible();
  });
});

test.describe("login (CP-7)", () => {
  test("valid credentials on a fresh session land on the dashboard", async ({
    page,
    browser,
  }) => {
    // Create the account in this context (auto-logged-in after register)…
    const creds = await registerAdult(page);

    // …then log in from a clean, anonymous context (no refresh cookie, no
    // in-memory token) to exercise the real login form end-to-end.
    const ctx = await browser.newContext();
    const fresh = await ctx.newPage();
    await loginAs(fresh, creds);
    await expect(fresh).toHaveURL(/\/dashboard$/);
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
    // not navigated into the app.
    await expect(fresh.getByRole("alert")).toBeVisible();
    await expect(fresh).toHaveURL(/\/login$/);
    await ctx.close();
  });
});

test.describe("registration errors", () => {
  test("a duplicate email is rejected with an error and stays on /register", async ({
    page,
    browser,
  }) => {
    const creds = await registerAdult(page);

    const ctx = await browser.newContext();
    const fresh = await ctx.newPage();
    await fillRegisterForm(fresh, {
      email: creds.email,
      dob: "1995-01-01",
      userType: "working",
      schoolLevel: "none",
      password: TEST_PASSWORD,
    });
    await fresh.getByRole("button", { name: "Đăng ký", exact: true }).click();

    await expect(fresh.getByRole("alert")).toBeVisible();
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
