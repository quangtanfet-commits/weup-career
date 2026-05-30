import type { CompetencyArea, Depth } from "@/lib/api/endpoints/progress";

/**
 * K-A-R cognitive-depth model (spec §5 `Depth`, CP-8). The ordering
 * K < A < R is load-bearing: progress only ever advances, never regresses
 * within a cycle, so the UI must render the achieved depth as a *prefix* of the
 * K→A→R ladder and never offer a downgrade (architecture.md §7 CP-8).
 *
 * Rank 0 means "no progress yet" — there is no `Depth` member for it; absence is
 * represented by a `null`/missing `depth_achieved`, mirroring the backend (which
 * stores no `LearnerProgress` row).
 */
export const DEPTHS: readonly Depth[] = ["K", "A", "R"] as const;

const DEPTH_RANK: Record<Depth, number> = { K: 1, A: 2, R: 3 };

/** Numeric rank of an achieved depth; `null`/absent → 0 (no progress). */
export function depthRank(depth: Depth | null | undefined): number {
  return depth ? DEPTH_RANK[depth] : 0;
}

/**
 * Whether `step` is at or below the achieved depth — i.e. this rung of the
 * K→A→R ladder is "reached". Used to colour the stepper/viz so the achieved
 * portion is filled and the rest is pending (color+icon+text, never colour
 * alone — architecture.md §8).
 */
export function isDepthReached(
  step: Depth,
  achieved: Depth | null | undefined,
): boolean {
  return depthRank(step) <= depthRank(achieved);
}

/** The fraction (0..1) of the K→A→R ladder a learner has reached for a competency. */
export function depthProgressRatio(achieved: Depth | null | undefined): number {
  return depthRank(achieved) / DEPTHS.length;
}

/**
 * The three ABCD competency areas in their canonical display order (spec §5
 * `CompetencyArea`, ADR-013). The CompetencyTree groups the 12 competencies
 * under these headings; the order is fixed (A→B→C) so the tree is stable.
 */
export const COMPETENCY_AREAS: readonly CompetencyArea[] = [
  "A_personal",
  "B_exploration",
  "C_building",
] as const;

/**
 * Group items carrying an `area` tag into the canonical A→B→C buckets, dropping
 * empty areas. Pure helper shared by CompetencyTree (competencies) and the
 * dev-phase panel (progress rows) so both render the same stable ordering.
 */
export function groupByArea<T extends { area: CompetencyArea }>(
  items: readonly T[],
): { area: CompetencyArea; items: T[] }[] {
  return COMPETENCY_AREAS.map((area) => ({
    area,
    items: items.filter((item) => item.area === area),
  })).filter((group) => group.items.length > 0);
}
