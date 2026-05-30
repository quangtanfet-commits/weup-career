import { expect, test } from "@playwright/test";

/**
 * F6 — wellbeing slice (architecture.md §3, §10, §11; FR-70/FR-71, NL4).
 *
 * These cover the authenticated wellbeing area: the supportive (non-clinical)
 * content, the always-visible safe path to a counselor, and the
 * support-request flow (create → confirmation → appears in "my requests").
 *
 * The flow is self-contained: it registers a fresh ADULT account
 * (`user_type=working`, date_of_birth ≥16y ago) through the real UI, so it does
 * NOT depend on a pre-seeded user and is NOT consent-gated. Registration +
 * login are public endpoints, so the only stack requirement is the full
 * `docker-compose.test.yml` topology (nginx + backend + frontend) that the F2
 * suite already brings up in CI.
 *
 * SEED/STACK NOTE: there is intentionally no seeded under-16 + active-consent
 * fixture in `docker-compose.test.yml`, so the consent-gated variant of this
 * flow (a child <16 seeing the soft gate instead of the form) is NOT exercised
 * here end-to-end. It is covered by the vitest component tests
 * (`consent-gate-banner.test.tsx`). If an authed under-16-with-consent fixture
 * is added later, a gated-path E2E can be appended.
 */

function uniqueEmail(): string {
  const rand = Math.random().toString(36).slice(2, 10);
  return `f6-wellbeing-${Date.now()}-${rand}@example.vn`;
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

test.describe("wellbeing — support request (authenticated adult)", () => {
  test("shows the non-clinical content and safe counselor path", async ({
    page,
  }) => {
    await registerAdult(page);
    await page.goto("/wellbeing");

    await expect(
      page.getByRole("heading", { level: 3, name: "Sức khỏe tinh thần" }),
    ).toBeVisible();

    // The safe path to a human counselor is always visible (FR-71).
    await expect(
      page.getByRole("heading", {
        name: "Kết nối với chuyên viên tư vấn học đường",
      }),
    ).toBeVisible();

    // Explicit non-clinical reassurance — the UI never diagnoses (NG-03).
    await expect(
      page.getByText(/không chẩn đoán hay đánh giá y tế/),
    ).toBeVisible();
  });

  test("creates a support request and sees it in 'my requests'", async ({
    page,
  }) => {
    await registerAdult(page);
    await page.goto("/wellbeing");

    const message = "Dạo này em thấy hơi mệt và muốn nói chuyện với ai đó.";
    await page.getByLabel("Bạn muốn chia sẻ điều gì?").fill(message);
    await page.getByRole("button", { name: "Gửi yêu cầu" }).click();

    // Confirmation routes the learner to a human, never an assessment result.
    await expect(
      page.getByText(/Một chuyên viên tư vấn sẽ sớm liên hệ với bạn/),
    ).toBeVisible();

    // The new request appears in the learner's own list.
    await expect(page.getByText(message)).toBeVisible();
  });

  test("validates an empty message before submitting", async ({ page }) => {
    await registerAdult(page);
    await page.goto("/wellbeing");

    await page.getByRole("button", { name: "Gửi yêu cầu" }).click();

    await expect(
      page.getByText(
        "Hãy chia sẻ đôi điều để chúng tôi kết nối bạn với người hỗ trợ",
      ),
    ).toBeVisible();
  });
});
