import { describe, it, expect } from "vitest";

import { loginSchema, toLoginPayload } from "@/features/auth/login.schema";

describe("loginSchema", () => {
  it("trims and lowercases the email", () => {
    const result = loginSchema.safeParse({
      email: "  Hoc.Sinh@Example.VN  ",
      password: "secret",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.email).toBe("hoc.sinh@example.vn");
    }
  });

  it("rejects an empty password", () => {
    const result = loginSchema.safeParse({
      email: "a@b.vn",
      password: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid email", () => {
    const result = loginSchema.safeParse({
      email: "not-an-email",
      password: "x",
    });
    expect(result.success).toBe(false);
  });
});

describe("toLoginPayload", () => {
  it("maps to the backend LoginRequest shape", () => {
    expect(toLoginPayload({ email: "a@b.vn", password: "pw" })).toEqual({
      email: "a@b.vn",
      password: "pw",
    });
  });
});
