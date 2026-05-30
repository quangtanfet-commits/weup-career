import { describe, it, expect, beforeEach } from "vitest";

import {
  useAuthStore,
  getAccessToken,
  type SessionUser,
} from "@/lib/auth/store";

const user: SessionUser = {
  id: "u1",
  email: "hoc.sinh@example.vn",
  roles: ["student"],
  age_band: "under_16",
  account_status: "pending_guardian_consent",
};

describe("auth store (in-memory token)", () => {
  beforeEach(() => {
    useAuthStore.getState().clearSession();
  });

  it("starts anonymous with no token", () => {
    const state = useAuthStore.getState();
    expect(state.status).toBe("anonymous");
    expect(state.accessToken).toBeNull();
    expect(getAccessToken()).toBeNull();
  });

  it("stores the access token in memory and exposes it via getAccessToken", () => {
    useAuthStore.getState().setSession("jwt-access-token", user);
    const state = useAuthStore.getState();
    expect(state.status).toBe("authenticated");
    expect(state.user?.email).toBe("hoc.sinh@example.vn");
    expect(getAccessToken()).toBe("jwt-access-token");
  });

  it("clears the session back to anonymous", () => {
    useAuthStore.getState().setSession("jwt", user);
    useAuthStore.getState().clearSession();
    const state = useAuthStore.getState();
    expect(state.status).toBe("anonymous");
    expect(state.accessToken).toBeNull();
    expect(state.user).toBeNull();
  });

  it("does NOT persist the token to localStorage (no persist middleware)", () => {
    useAuthStore.getState().setSession("secret-jwt", user);
    // The store must never write the token anywhere durable.
    const dump = JSON.stringify({ ...localStorage });
    expect(dump).not.toContain("secret-jwt");
  });
});
