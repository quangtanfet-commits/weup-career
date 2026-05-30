import { describe, it, expect, beforeEach } from "vitest";

import {
  useAuthStore,
  getAccessToken,
  toSessionUser,
  type SessionUser,
  type BackendUser,
} from "@/lib/auth/store";
import { encodeTestToken } from "./helpers/jwt";

const user: SessionUser = {
  id: "u1",
  email: "hoc.sinh@example.vn",
  roles: ["student"],
  age_band: "under_16",
  account_status: "pending_guardian_consent",
};

const backendUser: BackendUser = {
  id: "u2",
  email: "nguoi.di.lam@example.vn",
  age_band: "adult",
  account_status: "active",
  user_type: "working",
  school_level: "tertiary",
};

describe("auth store (in-memory token)", () => {
  it("starts in the pre-bootstrap loading state with no token", () => {
    // Read the default state BEFORE any clearSession so we observe the initial
    // value the app boots with (so guards can wait for the silent refresh).
    const initial = useAuthStore.getInitialState();
    expect(initial.status).toBe("loading");
    expect(initial.accessToken).toBeNull();
    expect(initial.user).toBeNull();
  });

  describe("after bootstrap resolves", () => {
    beforeEach(() => {
      useAuthStore.getState().clearSession();
    });

    it("clearSession resolves to anonymous with no token", () => {
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

    it("setSessionFromToken derives roles from token claims", () => {
      const token = encodeTestToken({ roles: ["working", "verified_adult"] });
      useAuthStore.getState().setSessionFromToken(token, backendUser);
      const state = useAuthStore.getState();
      expect(state.status).toBe("authenticated");
      expect(state.user?.roles).toEqual(["working", "verified_adult"]);
      expect(state.user?.account_status).toBe("active");
      expect(getAccessToken()).toBe(token);
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

  describe("finishLoading", () => {
    it("moves loading → anonymous", () => {
      useAuthStore.setState({
        status: "loading",
        accessToken: null,
        user: null,
      });
      useAuthStore.getState().finishLoading();
      expect(useAuthStore.getState().status).toBe("anonymous");
    });

    it("does not clobber an already-authenticated session", () => {
      useAuthStore.getState().setSession("jwt", user);
      useAuthStore.getState().finishLoading();
      const state = useAuthStore.getState();
      expect(state.status).toBe("authenticated");
      expect(state.accessToken).toBe("jwt");
    });
  });

  describe("toSessionUser", () => {
    it("falls back to [user_type] when the token has no roles claim", () => {
      const token = encodeTestToken({ sub: "u2" });
      const session = toSessionUser(token, backendUser);
      expect(session.roles).toEqual(["working"]);
      expect(session.id).toBe("u2");
      expect(session.email).toBe("nguoi.di.lam@example.vn");
    });
  });
});
