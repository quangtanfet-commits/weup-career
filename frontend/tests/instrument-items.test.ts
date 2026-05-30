import { describe, it, expect } from "vitest";

import {
  itemsFor,
  instrumentNameVi,
  instrumentBlurbVi,
  interpretResult,
  LIKERT_LABELS_VI,
  LIKERT_MIN,
  LIKERT_MAX,
} from "@/features/assessments/instrument-items";

describe("instrument item bank", () => {
  it("exposes a 1..5 Likert scale with five anchor labels", () => {
    expect(LIKERT_MIN).toBe(1);
    expect(LIKERT_MAX).toBe(5);
    expect(LIKERT_LABELS_VI).toHaveLength(5);
  });

  it("returns one item per RIASEC dimension keyed <DIM>_<n>", () => {
    const items = itemsFor("riasec");
    expect(items.map((i) => i.key)).toEqual([
      "R_1",
      "I_1",
      "A_1",
      "S_1",
      "E_1",
      "C_1",
    ]);
    // Every prompt is Vietnamese copy, never the bare dimension letter.
    for (const item of items) {
      expect(item.prompt_vi.length).toBeGreaterThan(5);
    }
  });

  it("returns the VIPS and MBTI banks", () => {
    expect(itemsFor("vips").map((i) => i.key)).toEqual([
      "V_1",
      "I_1",
      "P_1",
      "S_1",
    ]);
    expect(itemsFor("mbti").map((i) => i.key)).toEqual([
      "E_1",
      "I_1",
      "S_1",
      "N_1",
      "T_1",
      "F_1",
      "J_1",
      "P_1",
    ]);
  });

  it("gives a Vietnamese name and blurb for each instrument", () => {
    for (const type of ["riasec", "vips", "mbti"] as const) {
      expect(instrumentNameVi(type)).toBeTruthy();
      expect(instrumentBlurbVi(type)).toBeTruthy();
    }
    expect(instrumentNameVi("riasec")).toContain("RIASEC");
    expect(instrumentNameVi("mbti")).toContain("MBTI");
  });
});

describe("interpretResult (FR-12 non-prescriptive)", () => {
  it("sorts RIASEC scores high→low and maps the code to career-group links", () => {
    const result = interpretResult("riasec", {
      type: "riasec",
      scores: { R: 2, I: 5, A: 1, S: 4, E: 3, C: 0 },
      code: "ISE",
    });

    expect(result.code).toBe("ISE");
    // Sorted descending by score.
    expect(result.scores.map(([, score]) => score)).toEqual([5, 4, 3, 2, 1, 0]);
    // The top label is the Investigative group (highest score, 5).
    expect(result.scores[0]![0]).toContain("Investigative");
    // One link per code letter, all pointing at the careers filter.
    expect(result.careerGroups.map((g) => g.code)).toEqual(["I", "S", "E"]);
    expect(result.careerGroups[0]!.href).toBe("/careers?riasec=I");
  });

  it("ignores non-RIASEC letters in the code when building links", () => {
    const result = interpretResult("riasec", {
      type: "riasec",
      scores: { R: 1 },
      code: "RZ9",
    });
    expect(result.careerGroups.map((g) => g.code)).toEqual(["R"]);
  });

  it("uses `dominant` as the code for MBTI and emits no career links", () => {
    const result = interpretResult("mbti", {
      type: "mbti",
      scores: { E: 3, I: 1 },
      dominant: "ENTJ",
    });
    expect(result.code).toBe("ENTJ");
    expect(result.careerGroups).toHaveLength(0);
    // MBTI dimension labels stay as the raw axis letters.
    expect(result.scores[0]![0]).toBe("E");
  });

  it("degrades to an empty interpretation on schema drift", () => {
    const result = interpretResult("riasec", { type: "riasec" });
    expect(result.code).toBeUndefined();
    expect(result.scores).toHaveLength(0);
    expect(result.careerGroups).toHaveLength(0);
  });

  it("skips non-numeric score values defensively", () => {
    const result = interpretResult("vips", {
      type: "vips",
      scores: { V: 3, I: "bad" },
    });
    expect(result.scores).toEqual([["V", 3]]);
  });
});
