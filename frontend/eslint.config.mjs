// ESLint flat config. Next 16's `eslint-config-next` ships flat config only and
// peers `eslint >=9`, so the legacy `.eslintrc.json` no longer loads (it threw a
// circular-structure error against the flat plugin shape). See
// docs/frontend/migrations/next-16.md § ESLint flat-config migration.
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";
import storybook from "eslint-plugin-storybook";

const config = [
  {
    // node_modules is ignored by default in flat config; these are the project
    // additions that mirror the old `ignorePatterns`.
    ignores: ["lib/api/schema.ts", ".next/**", "storybook-static/**"],
  },
  ...nextCoreWebVitals,
  ...nextTypescript,
  ...storybook.configs["flat/recommended"],
  {
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
    },
  },
];

export default config;
