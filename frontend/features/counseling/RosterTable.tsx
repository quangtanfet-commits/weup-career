"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";

import type { RosterEntryOut } from "@/lib/api/endpoints/counseling";

/**
 * De-sensitized student roster (architecture.md §3, §4.4; FR-82, CP-3). Renders
 * only the de-sensitized `RosterEntryOut` shape — email + class, never any
 * assessment payload. Each row links to the student's de-sensitized view.
 *
 * Presentational: loading / [CRED_0581ACFA] / [CRED_E91DDC68] (incl. the neutral CP-4 not-found
 * state) are decided by the page from the query result, so this component just
 * renders a non-empty list.
 */
export function RosterTable({
  entries,
}: {
  entries: readonly RosterEntryOut[];
}) {
  const t = useTranslations("counselor");

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <caption className="sr-only">{t("rosterCaption")}</caption>
        <thead>
          <tr className="border-b border-input text-left text-ink-600">
            <th scope="col" className="px-3 py-2 font-medium">
              {t("rosterEmail")}
            </th>
            <th scope="col" className="px-3 py-2 font-medium">
              {t("rosterClass")}
            </th>
            <th scope="col" className="px-3 py-2 font-medium">
              <span className="sr-only">{t("rosterActions")}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr
              key={entry.user_id}
              className="border-b border-input/60 last:border-0"
            >
              <td className="px-3 py-2 text-ink-900">{entry.email}</td>
              <td className="px-3 py-2 text-ink-600">
                {entry.class_id ?? t("rosterNoClass")}
              </td>
              <td className="px-3 py-2 text-right">
                <Link
                  href={`/counselor/students/${encodeURIComponent(entry.user_id)}`}
                  className="font-medium text-secondary-700 underline-offset-2 hover:underline"
                >
                  {t("rosterView")}
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
