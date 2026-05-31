import { expect, test } from "@playwright/test";

import { registerAdult } from "./fixtures/auth";

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
