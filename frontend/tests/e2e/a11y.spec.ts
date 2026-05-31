import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

/**
 * WCAG 2.1 AA accessibility gate (enterprise-saas-validate full-stack profile).
 *
 * Scans the anonymous, server-rendered surface — the pages a logged-out visitor
 * (including search engines and assistive tech) reaches without a seeded account.
 * Authenticated dashboards are covered separately once a login fixture lands.
 *
 * Gate: zero violations at the wcag2a / wcag2aa / wcag21a / wcag21aa tags.
 * A genuine, reviewed exception must be added to KNOWN_EXCEPTIONS with a tracked
 * rule id + justification — never by lowering the tag set.
 */

const ANON_ROUTES = [
  { path: "/", name: "home" },
  { path: "/careers", name: "career library" },
  { path: "/content", name: "content library" },
  { path: "/login", name: "login" },
  { path: "/register", name: "register" },
] as const;

// Reviewed, justified waivers keyed by axe rule id. Empty = no waived rules.
// Each entry MUST carry a reason and an owner/deadline so it cannot rot silently.
const KNOWN_EXCEPTIONS: { rule: string; reason: string }[] = [];

const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

for (const route of ANON_ROUTES) {
  test(`a11y: ${route.name} (${route.path}) has no WCAG A/AA violations`, async ({
    page,
  }) => {
    await page.goto(route.path);
    // Wait for the primary heading so we scan a settled DOM, not a mid-hydration
    // frame. Auth pages (login/register) use a Card <h3> title and have no <h1>,
    // so match any heading level rather than assuming a level-1 landing heading.
    await expect(page.locator("h1, h2, h3").first()).toBeVisible();

    const builder = new AxeBuilder({ page }).withTags(WCAG_TAGS);
    const waived = KNOWN_EXCEPTIONS.map((e) => e.rule);
    if (waived.length) builder.disableRules(waived);

    const results = await builder.analyze();

    if (results.violations.length) {
      const summary = results.violations
        .map(
          (v) =>
            `  [${v.impact ?? "n/a"}] ${v.id}: ${v.help} (${v.nodes.length} node(s))\n` +
            `    ${v.helpUrl}`,
        )
        .join("\n");
      // Surface the full list in the failure message for triage.
      expect(
        results.violations,
        `axe violations on ${route.path}:\n${summary}`,
      ).toEqual([]);
    } else {
      expect(results.violations).toEqual([]);
    }
  });
}
