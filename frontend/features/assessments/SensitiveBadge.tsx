import { useTranslations } from "next-intl";

/**
 * "Dữ liệu riêng tư" badge (architecture.md §2.1, §4.4; CP-3). Marks a sensitive
 * surface (assessment results) with the dedicated `--color-sensitive-700` token
 * **plus** a lock icon **plus** text — never colour alone (a11y rule §2.1). The
 * icon is decorative (`aria-hidden`); the label carries the meaning for screen
 * readers.
 */
export function SensitiveBadge() {
  const t = useTranslations("assessment");
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border border-sensitive-700/30 bg-sensitive-700/10 px-3 py-1 text-xs font-medium text-sensitive-700"
      data-testid="sensitive-badge"
    >
      <svg
        aria-hidden="true"
        focusable="false"
        viewBox="0 0 16 16"
        className="h-3.5 w-3.5"
        fill="currentColor"
      >
        <path d="M8 1a3 3 0 0 0-3 3v2H4.5A1.5 1.5 0 0 0 3 7.5v5A1.5 1.5 0 0 0 4.5 14h7a1.5 1.5 0 0 0 1.5-1.5v-5A1.5 1.5 0 0 0 11.5 6H11V4a3 3 0 0 0-3-3Zm1.5 5h-3V4a1.5 1.5 0 0 1 3 0v2Z" />
      </svg>
      {t("sensitiveBadge")}
    </span>
  );
}
