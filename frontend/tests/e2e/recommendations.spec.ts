import { expect, test } from "@playwright/test";

/**
 * F5 — recommendations slice (architecture.md §3, §10 L5, §11; FR-60..63,
 * CP-5/CP-6).
 *
 * These cover the authenticated recommendations entry page: that it loads for a
 * signed-in adult, that the consent gate is ABSENT for an adult (not a child
 * <16), and that the human-in-the-loop rule (CP-5) is stated up front before
 * any suggestion is produced.
 *
 * The flow is self-contained: it registers a fresh ADULT account
 * (`user_type=working`, date_of_birth ≥16y ago) through the real UI, so it does
 * NOT depend on a pre-seeded user and is NOT consent-gated. Registration +
 * login are public endpoints, so the only stack requirement is the full
 * `docker-compose.test.yml` topology (nginx + backend + frontend) that the F2
 * suite already brings up in CI.
 *
 * SEED/STACK NOTE — what is and is NOT exercised E2E, and why:
 *   - Generating a recommendation (`POST /recommendations`) depends on the
 *     learner already having assessment results + competency progress for the
 *     engine to reason over (FR-60). A freshly self-registered adult has none of
 *     that data, and `docker-compose.test.yml` seeds no such fixture, so the
 *     happy path generate → rationale (CP-6) → confirm (CP-5) → confirmed-state
 *     is NOT driven end-to-end here; it would be non-deterministic (the backend
 *     may legitimately 422/409 with no input data). It is fully covered by the
 *     vitest component tests: `recommendation-card.test.tsx` (CP-6 mandatory
 *     rationale + missing-rationale error state, CP-5 unconfirmed "chưa có hiệu
 *     lực" vs confirmed state) and `human-confirm-action.test.tsx` (no confirm
 *     call until an explicit click; the posted decision).
 *   - What IS exercised here: the page loads for an authed adult, the consent
 *     gate is absent (CP-1 only applies to children <16), and the CP-5
 *     human-in-the-loop notice + generate affordance are present. If a seeded
 *     under-16-with-consent + assessment/progress fixture is added later, a
 *     gated/generate E2E can be appended.
 */

function uniqueEmail(): string {
  const rand = Math.random().toString(36).slice(2, 10);
  return `f5-reco-${Date.now()}-${rand}@example.vn`;
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

test.describe("recommendations — entry page (authenticated adult)", () => {
  test("loads the entry page with no consent gate and states the human-in-the-loop rule", async ({
    page,
  }) => {
    await registerAdult(page);
    await page.goto("/recommendations");

    // Page heading is visible.
    await expect(
      page.getByRole("heading", { level: 1, name: "Gợi ý hướng nghiệp" }),
    ).toBeVisible();

    // CP-5: the human-in-the-loop rule is stated before any suggestion is made.
    await expect(
      page.getByText(
        /Hệ thống không tự thực hiện bất kỳ quyết định phân luồng nào/,
      ),
    ).toBeVisible();

    // The generate affordance is present (it only produces a suggestion).
    await expect(page.getByRole("button", { name: "Tạo gợi ý" })).toBeVisible();

    // CP-1: an adult is not consent-gated — the gate CTA must be absent.
    await expect(
      page.getByRole("link", { name: "Mời người giám hộ" }),
    ).toHaveCount(0);
  });
});
