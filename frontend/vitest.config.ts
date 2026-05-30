import { resolve } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

/**
 * Vitest runs independently of the Next.js runtime (architecture.md §1): it
 * transforms tests with its own esbuild/Vite pipeline. The `@/*` alias mirrors
 * tsconfig so imports resolve identically in tests and app code.
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "."),
      // `server-only` throws outside the Next server runtime; stub it so RSC
      // modules can be unit-tested with a mocked fetch.
      "server-only": resolve(__dirname, "tests/stubs/server-only.ts"),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      // Scope coverage to modules with real logic. Static presentational
      // chrome (route-group layouts, placeholder pages, the marketing home) is
      // exercised end-to-end by the build + Playwright, not unit asserts — so
      // it is excluded rather than padded with trivial render tests. The
      // load-bearing RSC demo page (nghe-nghiep) and all of lib/* stay in scope.
      include: [
        "components/**/*.{ts,tsx}",
        "features/**/*.{ts,tsx}",
        "lib/**/*.{ts,tsx}",
        "app/(public)/nghe-nghiep/**/*.{ts,tsx}",
        "app/(public)/careers/**/*.{ts,tsx}",
        "app/(public)/content/**/*.{ts,tsx}",
      ],
      exclude: [
        "lib/api/schema.ts",
        "lib/i18n/request.ts",
        "**/*.d.ts",
      ],
      thresholds: {
        statements: 90,
        branches: 90,
        functions: 90,
        lines: 90,
      },
    },
  },
});
