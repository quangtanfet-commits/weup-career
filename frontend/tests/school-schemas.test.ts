import { describe, it, expect } from "vitest";

import {
  createClassSchema,
  toCreateClassPayload,
} from "@/features/school/create-class.schema";
import {
  ASSIGNABLE_ROLES,
  assignMemberSchema,
  toAssignMemberPayload,
} from "@/features/school/assign-member.schema";

describe("create-class schema", () => {
  it("rejects an empty name and grade", () => {
    const r = createClassSchema.safeParse({ name: "  ", grade: "" });
    expect(r.success).toBe(false);
  });

  it("maps valid values to the CreateClassRequest payload", () => {
    const values = createClassSchema.parse({ name: "10A1", grade: "10" });
    expect(toCreateClassPayload(values)).toEqual({ name: "10A1", grade: "10" });
  });
});

describe("assign-member schema", () => {
  it("only allows assignable school roles (no school_admin)", () => {
    expect(ASSIGNABLE_ROLES).toEqual(["student", "counselor"]);
    expect(
      assignMemberSchema.safeParse({
        user_id: "u1",
        role: "school_admin",
      }).success,
    ).toBe(false);
  });

  it("requires a user id", () => {
    expect(
      assignMemberSchema.safeParse({ user_id: "", role: "student" }).success,
    ).toBe(false);
  });

  it("maps an empty class_id to null (no class scoping)", () => {
    const values = assignMemberSchema.parse({
      user_id: "u1",
      role: "counselor",
      class_id: "",
    });
    expect(toAssignMemberPayload(values)).toEqual({
      user_id: "u1",
      role: "counselor",
      class_id: null,
    });
  });

  it("keeps a provided class_id", () => {
    const values = assignMemberSchema.parse({
      user_id: "u1",
      role: "student",
      class_id: "c9",
    });
    expect(toAssignMemberPayload(values).class_id).toBe("c9");
  });
});
