/**
 * i18n configuration (architecture.md §9). Vietnamese is the default and only
 * shipped locale in F1; the structure leaves room to add `/en` later without
 * breaking routes (UI-chrome strings live in `messages/<locale>.json`).
 */
export const locales = ["vi"] as const;
export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "vi";

export function isLocale(value: string): value is Locale {
  return (locales as readonly string[]).includes(value);
}
