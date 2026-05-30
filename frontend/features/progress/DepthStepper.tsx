"use client";

import { useTranslations } from "next-intl";

import { cn } from "@/lib/utils";
import type { Depth } from "@/lib/api/endpoints/progress";
import { DEPTHS, depthRank, isDepthReached } from "@/lib/progress/depth";

/**
 * K→A→R depth stepper (architecture.md §11, CP-8). Renders the three rungs of
 * the cognitive-depth ladder for one competency, filling the portion the learner
 * has *reached* and leaving the rest pending.
 *
 * CP-8 (monotonicity) is load-bearing in the UI: this is a read-only display of
 * the achieved prefix — there is NO control to select/downgrade a depth. The
 * achieved state is conveyed by color + a check/empty icon + the Vietnamese
 * label (never colour alone — architecture.md §8 accessibility).
 */
export function DepthStepper({
  achieved,
  className,
}: {
  achieved: Depth | null | undefined;
  className?: string;
}) {
  const t = useTranslations("progress");
  const achievedRank = depthRank(achieved);

  return (
    <ol
      className={cn("flex items-stretch gap-2", className)}
      aria-label={t("overviewHeading")}
    >
      {DEPTHS.map((step) => {
        const reached = isDepthReached(step, achieved);
        const isCurrent = depthRank(step) === achievedRank;
        const stateLabel = reached ? t("achievedLabel") : t("notYetLabel");
        return (
          <li key={step} className="flex flex-1 flex-col gap-1">
            <div
              aria-hidden="true"
              className={cn(
                "h-1.5 rounded-full",
                reached ? "bg-success-600" : "bg-ink-600/15",
              )}
            />
            <div className="flex items-center gap-1.5">
              <span
                aria-hidden="true"
                className={cn(
                  "inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold",
                  reached
                    ? "bg-success-600 text-white"
                    : "border border-ink-600/30 text-ink-600",
                )}
              >
                {reached ? "✓" : ""}
              </span>
              <span
                className={cn(
                  "text-xs font-medium",
                  reached ? "text-ink-900" : "text-ink-600",
                  isCurrent && reached && "underline",
                )}
              >
                {t(`depth.${step}`)}
              </span>
              {/* Screen-reader-only state so meaning isn't colour-only. */}
              <span className="sr-only">{`(${stateLabel})`}</span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
