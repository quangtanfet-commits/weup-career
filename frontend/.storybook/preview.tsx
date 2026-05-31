import type { Preview } from "@storybook/nextjs-vite";

// Load the app's Tailwind layer + design tokens so stories render with the same
// styling as production (Chromatic then pixel-diffs the real surfaces, not bare
// unstyled DOM). Mirrors app/layout.tsx's `import "@/styles/globals.css"`.
import "@/styles/globals.css";

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    a11y: {
      // 'error' fails the Storybook a11y run on violations; 'todo' only surfaces
      // them in the UI. We keep authoritative WCAG gating in the axe-core E2E
      // spec (tests/e2e/a11y.spec.ts), so here a11y is advisory in the panel.
      test: "todo",
    },
  },
};

export default preview;
