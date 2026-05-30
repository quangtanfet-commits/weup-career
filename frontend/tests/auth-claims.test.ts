import { describe, it, expect } from "vitest";

import { decodeAccessTokenClaims, rolesFromToken } from "@/lib/auth/claims";
import { encodeTestToken } from "./helpers/jwt";

describe("decodeAccessTokenClaims", () => {
  it("decodes a well-formed token payload", () => {
    const token = encodeTestToken({
      sub: "u1",
      email: "hoc.sinh@example.vn",
      user_type: "student",
      account_status: "pending_guardian_consent",
      age_band: "under_16",
      roles: ["student"],
    });
    const claims = decodeAccessTokenClaims(token);
    expect(claims.sub).toBe("u1");
    expect(claims.email).toBe("hoc.sinh@example.vn");
    expect(claims.user_type).toBe("student");
    expect(claims.age_band).toBe("under_16");
    expect(claims.roles).toEqual(["student"]);
  });

  it("preserves non-ASCII (Vietnamese) claim values", () => {
    const token = encodeTestToken({ email: "Nguyễn Văn Á" });
    expect(decodeAccessTokenClaims(token).email).toBe("Nguyễn Văn Á");
  });

  it("returns an empty object for a token with too few segments", () => {
    expect(decodeAccessTokenClaims("not-a-jwt")).toEqual({});
  });

  it("returns an empty object when the payload segment is not valid base64/JSON", () => {
    expect(decodeAccessTokenClaims("aaa.!!!!.bbb")).toEqual({});
  });

  it("returns an empty object when the payload is JSON but not an object", () => {
    const token = `aaa.${btoa("42")}.bbb`;
    expect(decodeAccessTokenClaims(token)).toEqual({});
  });

  it("returns an empty object when the decoded payload is not valid JSON", () => {
    // Valid base64url that decodes to plain text (not JSON) → JSON.parse throws.
    const token = `aaa.${btoa("hello world")}.bbb`;
    expect(decodeAccessTokenClaims(token)).toEqual({});
  });
});

describe("rolesFromToken", () => {
  it("prefers the signed roles claim", () => {
    const token = encodeTestToken({ roles: ["student", "verified"] });
    expect(rolesFromToken(token)).toEqual(["student", "verified"]);
  });

  it("filters non-string entries out of the roles claim", () => {
    const token = encodeTestToken({ roles: ["student", 7, null] });
    expect(rolesFromToken(token)).toEqual(["student"]);
  });

  it("falls back to [user_type] from the claim when roles is absent", () => {
    const token = encodeTestToken({ user_type: "working" });
    expect(rolesFromToken(token)).toEqual(["working"]);
  });

  it("falls back to the provided fallbackUserType when the token has neither", () => {
    const token = encodeTestToken({ sub: "u1" });
    expect(rolesFromToken(token, "student")).toEqual(["student"]);
  });

  it("returns [] for a null token with no fallback", () => {
    expect(rolesFromToken(null)).toEqual([]);
  });
});
