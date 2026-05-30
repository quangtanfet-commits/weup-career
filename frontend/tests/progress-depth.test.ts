import { describe, it, expect } from "vitest";

import type { CompetencyArea, Depth } from "@/lib/api/endpoints/progress";
import {
  COMPETENCY_AREAS,
  DEPTHS,
  depthProgressRatio,
  depthRank,
  groupByArea,
  isDepthReached,
} from "@/lib/progress/depth";

describe("depth model (K-A-R, CP-8)", () => {
  it("exposes the ladder in K→A→R order", () => {
    expect(DEPTHS).toEqual(["K", "A", "R"]);
  });

  it("ranks K<A<R with 0 for no progress", () => {
    expect(depthRank("K")).toBe(1);
    expect(depthRank("A")).toBe(2);
    expect(depthRank("R")).toBe(3);
    expect(depthRank(null)).toBe(0);
    expect(depthRank(undefined)).toBe(0);
  });

  it("isDepthReached treats achieved depth as a K→A→R prefix", () => {
    // Achieved A → K and A reached, R not (monotonic prefix).
    expect(isDepthReached("K", "A")).toBe(true);
    expect(isDepthReached("A", "A")).toBe(true);
    expect(isDepthReached("R", "A")).toBe(false);
    // No progress → nothing reached.
    expect(isDepthReached("K", null)).toBe(false);
  });

  it("depthProgressRatio is reached/total", () => {
    expect(depthProgressRatio(null)).toBe(0);
    expect(depthProgressRatio("K")).toBeCloseTo(1 / 3);
    expect(depthProgressRatio("R")).toBe(1);
  });

  it("groups items into the canonical A→B→C order, dropping empty areas", () => {
    const items: { area: CompetencyArea; id: string }[] = [
      { area: "C_building", id: "c1" },
      { area: "A_personal", id: "a1" },
      { area: "A_personal", id: "a2" },
    ];

    const groups = groupByArea(items);

    // B_exploration has no items → dropped; A before C preserved.
    expect(groups.map((g) => g.area)).toEqual(["A_personal", "C_building"]);
    expect(groups[0]!.items.map((i) => i.id)).toEqual(["a1", "a2"]);
    expect(COMPETENCY_AREAS).toEqual([
      "A_personal",
      "B_exploration",
      "C_building",
    ]);
  });

  it("every Depth member has a positive rank (exhaustive)", () => {
    for (const d of DEPTHS as readonly Depth[]) {
      expect(depthRank(d)).toBeGreaterThan(0);
    }
  });
});
