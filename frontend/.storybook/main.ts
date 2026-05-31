import type { StorybookConfig } from "@storybook/nextjs-vite";

/**
 * Storybook config (full-stack validation gap 5). Stories live next to the
 * reusable primitives under components/** plus the curated set in stories/**.
 * Framework is the Vite builder (@storybook/nextjs-vite) so `build-storybook`
 * is deterministic and headless — no webpack dev server needed for CI.
 *
 * The @storybook/addon-vitest browser-test integration that `storybook init`
 * wired into vitest.config.ts was intentionally reverted: it spins up a
 * Playwright browser runner that needs system deps absent in this devcontainer
 * and would destabilise the existing jsdom unit suite + 90% coverage gate the
 * native harness runs. A11y is still covered (addon-a11y here + the anonymous
 * axe-core E2E spec); visual regression is Chromatic (see chromatic note).
 */
const config: StorybookConfig = {
  stories: [
    "../stories/**/*.mdx",
    "../stories/**/*.stories.@(js|jsx|mjs|ts|tsx)",
    "../components/**/*.stories.@(js|jsx|mjs|ts|tsx)",
  ],
  addons: [
    "@chromatic-com/storybook",
    "@storybook/addon-a11y",
    "@storybook/addon-docs",
  ],
  framework: "@storybook/nextjs-vite",
  staticDirs: ["../public"],
};
export default config;
