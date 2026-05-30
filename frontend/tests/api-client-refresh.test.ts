import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { apiFetch } from "@/lib/api/client";
import { useAuthStore, getAccessToken } from "@/lib/auth/store";
import { __resetSessionRestoreForTests } from "@/lib/auth/session-restore";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const refreshBody = {
  access_token: "new-token",
  expires_in: 900,
  token_type: "bearer",
  user: {
    id: "u1",
    email: "a@b.vn",
    account_status: "active",
    age_band: "adult",
    user_type: "working",
    school_level: "tertiary",
    created_at: "2026-01-01T00:00:00Z",
  },
};

describe("apiFetch refresh-on-401 interceptor (CP-7)", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    __resetSessionRestoreForTests();
    useAuthStore.getState().setSession("stale-token", {
      id: "u1",
      email: "a@b.vn",
      roles: ["working"],
    });
  });
  afterEach(() => {
    vi.restoreAllMocks();
    __resetSessionRestoreForTests();
    useAuthStore.getState().clearSession();
  });

  it("refreshes once and replays the original request with the new token", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      // 1) original request → 401
      .mockResolvedValueOnce(jsonResponse({ code: "UNAUTHORIZED" }, 401))
      // 2) POST /auth/refresh → 200 (sets the new session)
      .mockResolvedValueOnce(jsonResponse(refreshBody))
      // 3) replayed original request → 200
      .mockResolvedValueOnce(jsonResponse({ ok: true }));

    const result = await apiFetch<{ ok: boolean }>("/recommendations");

    expect(result).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledTimes(3);

    // The replay (call #3) must carry the refreshed bearer token.
    const retryInit = fetchMock.mock.calls[2]![1] as RequestInit;
    expect(new Headers(retryInit.headers).get("authorization")).toBe(
      "Bearer new-token",
    );
    expect(getAccessToken()).toBe("new-token");
  });

  it("notifies auth-lost and throws when the refresh itself fails", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      // 1) original → 401
      .mockResolvedValueOnce(jsonResponse({ code: "UNAUTHORIZED" }, 401))
      // 2) refresh → 401 (no valid cookie)
      .mockResolvedValueOnce(jsonResponse({ code: "UNAUTHORIZED" }, 401));

    await expect(apiFetch("/recommendations")).rejects.toMatchObject({
      status: 401,
    });
    // original + refresh, no replay
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(useAuthStore.getState().status).toBe("anonymous");
    expect(getAccessToken()).toBeNull();
  });

  it("gives up (no infinite retry) when the replay is still 401", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      // 1) original → 401
      .mockResolvedValueOnce(jsonResponse({ code: "UNAUTHORIZED" }, 401))
      // 2) refresh → 200 (new token issued)
      .mockResolvedValueOnce(jsonResponse(refreshBody))
      // 3) replay → 401 again
      .mockResolvedValueOnce(jsonResponse({ code: "UNAUTHORIZED" }, 401));

    await expect(apiFetch("/recommendations")).rejects.toMatchObject({
      status: 401,
      code: "UNAUTHORIZED",
    });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(useAuthStore.getState().status).toBe("anonymous");
  });

  it("does not intercept when skipAuthRefresh is set (used by /auth/refresh)", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ code: "UNAUTHORIZED" }, 401));

    await expect(
      apiFetch("/auth/refresh", { method: "POST", skipAuthRefresh: true }),
    ).rejects.toMatchObject({ status: 401 });
    // Exactly one call: no refresh recursion.
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
