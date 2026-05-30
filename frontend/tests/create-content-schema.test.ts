import { describe, it, expect } from "vitest";

import {
  createContentSchema,
  toCreateContentPayload,
} from "@/features/content/create-content.schema";

const valid = {
  title: "Hiểu về bản thân",
  body: "Nội dung minh họa.",
  competency_code: "NL1",
  dieu5_code: "b",
  depth: "K",
  dev_phase: "awareness",
  school_level: "lower_secondary",
} as const;

describe("create-content schema (FR-90 five mandatory tags)", () => {
  it("accepts a complete draft and maps to CreateContentRequest", () => {
    const values = createContentSchema.parse(valid);
    expect(toCreateContentPayload(values)).toEqual({
      ...valid,
      source_ref: "",
    });
  });

  it("rejects a missing competency_code (mandatory tag)", () => {
    expect(
      createContentSchema.safeParse({ ...valid, competency_code: "" }).success,
    ).toBe(false);
  });

  it("rejects an invalid depth enum", () => {
    expect(
      createContentSchema.safeParse({ ...valid, depth: "Z" }).success,
    ).toBe(false);
  });

  it("rejects an invalid school_level enum", () => {
    expect(
      createContentSchema.safeParse({ ...valid, school_level: "college" })
        .success,
    ).toBe(false);
  });

  it("defaults an omitted source_ref to an empty string in the payload", () => {
    const values = createContentSchema.parse(valid);
    expect(toCreateContentPayload(values).source_ref).toBe("");
  });
});
