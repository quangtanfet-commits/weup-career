import { Be_Vietnam_Pro } from "next/font/google";
import type { Preview } from "@storybook/nextjs-vite";

// Load the app's Tailwind layer + design tokens so stories render with the same
// styling as production (Chromatic then pixel-diffs the real surfaces, not bare
// unstyled DOM). Mirrors app/layout.tsx's `import "@/styles/globals.css"`.
import "@/styles/globals.css";

// Mirror app/layout.tsx's font wiring. Without this, `--font-be-vietnam-pro` is
// undefined in Storybook, `--font-sans` collapses to an invalid leading-comma
// value, and stories fall back to the UA font (Times New Roman) — see
// docs/frontend/migrations/tailwind-4.md. @storybook/nextjs-vite self-hosts the
// font at build time, so the render is deterministic (Chromatic-safe).
const beVietnamPro = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-be-vietnam-pro",
  display: "swap",
});

if (typeof document !== "undefined") {
  document.documentElement.classList.add(beVietnamPro.variable);
}

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
