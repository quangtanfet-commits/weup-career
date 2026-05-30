"use client";

import { useTranslations } from "next-intl";

import type { ProgressItem } from "@/lib/api/endpoints/progress";
import { depthRank } from "@/lib/progress/depth";
import { DepthStepper } from "./DepthStepper";

/**
 * K-A-R progress overview (architecture.md §11, FR-24). Renders every
 * competency the learner has progress on as a row with its current depth label
 * and a `DepthStepper`. This is the at-a-glance "how far along each competency"
 * view shown to the learner, a verified guardian (<16), and an assigned
 * counselor (FR-24) — all read-only.
 *
 * Accessibility (architecture.md §8): meaning is carried by the depth label +
 * the stepper's icon/text, never colour alone. Rendered as a definition-style
 * list so the (competency → current depth) mapping is announced by AT.
 */
export function KARProgressViz({ items }: { items: readonly ProgressItem[] }) {
  const t = useTranslations("progress");

  if (items.length === 0) {
    return <p className="text-sm text-ink-600">{t("empty")}</p>;
  }

  // Stable order: most-advanced competencies first, then by code for determinism.
  const ordered = [...items].sort(
    (a, b) =>
      depthRank(b.depth_achieved) - depthRank(a.depth_achieved) ||
      a.code.localeCompare(b.code),
  );

  return (
    <ul className="flex flex-col divide-y divide-ink-600/10">
      {ordered.map((item) => (
        <li
          key={item.competency_id}
          className="flex flex-col gap-2 py-4 sm:flex-row sm:items-center sm:justify-between sm:gap-6"
        >
          <div className="flex flex-col gap-0.5">
            <span className="text-sm font-medium text-ink-900">
              {item.name_vi}
            </span>
            <span className="text-xs text-ink-600">
              {t("currentDepthLabel")}:{" "}
              {item.depth_label_vi ?? t("noProgressYet")}
            </span>
          </div>
          <DepthStepper
            achieved={item.depth_achieved}
            className="w-full sm:w-64"
          />
        </li>
      ))}
    </ul>
  );
}
