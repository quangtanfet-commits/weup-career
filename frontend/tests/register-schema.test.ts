import { describe, it, expect } from "vitest";

import {
  registerSchema,
  toRegisterPayload,
  ageInYears,
  requiresGuardian,
  type RegisterFormValues,
} from "@/features/auth/register.schema";

const NOW = new Date("2026-05-30T00:00:00.000Z");

const valid: RegisterFormValues = {
  email: "Hoc.Sinh@Example.VN",
  password: "Abcdef12",
  confirmPassword: "Abcdef12",
  date_of_birth: "2008-01-01",
  school_level: "lower_secondary",
  user_type: "student",
};

describe("registerSchema", () => {
  it("accepts a valid payload and normalises the email", () => {
    const result = registerSchema.safeParse(valid);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.email).toBe("hoc.sinh@example.vn");
    }
  });

  it("rejects a password missing an uppercase letter", () => {
    const result = registerSchema.safeParse({
      ...valid,
      password: "abcdef12",
      confirmPassword: "abcdef12",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a password shorter than 8 characters", () => {
    const result = registerSchema.safeParse({
      ...valid,
      password: "Abc12",
      confirmPassword: "Abc12",
    });
    expect(result.success).toBe(false);
  });

  it("rejects when confirmPassword does not match", () => {
    const result = registerSchema.safeParse({
      ...valid,
      confirmPassword: "Different1",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0]?.path).toEqual(["confirmPassword"]);
    }
  });

  it("rejects a future date of birth", () => {
    const result = registerSchema.safeParse({
      ...valid,
      date_of_birth: "3000-01-01",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an unparseable date of birth", () => {
    const result = registerSchema.safeParse({
      ...valid,
      date_of_birth: "not-a-date",
    });
    expect(result.success).toBe(false);
  });
});

describe("toRegisterPayload", () => {
  it("drops confirmPassword and keeps the backend fields", () => {
    const payload = toRegisterPayload({ ...valid, email: "a@b.vn" });
    expect(payload).toEqual({
      email: "a@b.vn",
      password: "Abcdef12",
      date_of_birth: "2008-01-01",
      school_level: "lower_secondary",
      user_type: "student",
    });
    expect("confirmPassword" in payload).toBe(false);
  });
});

describe("ageInYears", () => {
  it("computes whole years", () => {
    expect(ageInYears("2010-05-30", NOW)).toBe(16);
  });

  it("does not count a birthday that has not occurred yet this year", () => {
    expect(ageInYears("2010-05-31", NOW)).toBe(15);
  });

  it("returns NaN for an invalid date", () => {
    expect(Number.isNaN(ageInYears("nope", NOW))).toBe(true);
  });
});

describe("requiresGuardian", () => {
  it("is true for a child under 16", () => {
    expect(requiresGuardian("2012-01-01", NOW)).toBe(true);
  });

  it("is false on the 16th birthday", () => {
    expect(requiresGuardian("2010-05-30", NOW)).toBe(false);
  });

  it("is false for an invalid date (no false guardian prompt)", () => {
    expect(requiresGuardian("nope", NOW)).toBe(false);
  });
});
