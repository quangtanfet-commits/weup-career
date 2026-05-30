import type { Config } from "tailwindcss";

/**
 * Design tokens map to the CSS variables declared in `styles/globals.css`
 * (architecture.md §2). shadcn/ui primitives read the same variables, so there
 * is a single source of truth for colour, radius, spacing and elevation.
 */
const config: Config = {
  darkMode: ["class", '[data-theme="dark"]'],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./features/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "var(--color-surface)",
        foreground: "var(--color-ink-900)",
        primary: {
          DEFAULT: "var(--color-primary-600)",
          foreground: "#ffffff",
          50: "var(--color-primary-50)",
          600: "var(--color-primary-600)",
          700: "var(--color-primary-700)",
        },
        secondary: {
          DEFAULT: "var(--color-secondary-500)",
          foreground: "#ffffff",
          500: "var(--color-secondary-500)",
          700: "var(--color-secondary-700)",
        },
        ink: {
          900: "var(--color-ink-900)",
          600: "var(--color-ink-600)",
        },
        success: { 600: "var(--color-success-600)" },
        warning: { 600: "var(--color-warning-600)" },
        danger: { 600: "var(--color-danger-600)" },
        sensitive: { 700: "var(--color-sensitive-700)" },
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
