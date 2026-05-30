import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  restoreSession,
  onAuthLost,
  notifyAuthLost,
  __resetSessionRestoreForTests,
} from "@/lib/auth/session-restore";
import { useAuthStore, getAccessToken } from "@/lib/auth/store";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const tokenResponse = {
  access_token: "fresh-token",
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

describe("restoreSession", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    __resetSessionRestoreForTests();
    useAuthStore.getState().clearSession();
  });
  afterEach(() => {
    vi.restoreAllMocks();
    __resetSessionRestoreForTests();
    useAuthStore.getState().clearSession();
  });

  it("calls POST /auth/refresh and sets the session on success", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(tokenResponse));

    const token = await restoreSession();

    expect(token).toBe("fresh-token");
    expect(getAccessToken()).toBe("fresh-token");
    expect(useAuthStore.getState().status).toBe("authenticated");
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/auth/refresh");
    expect((init as RequestInit).method).toBe("POST");
  });

  it("resolves to null without throwing when there is no valid cookie (401)", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ code: "UNAUTHORIZED" }, 401),
    );

    const token = await restoreSession();

    expect(token).toBeNull();
    expect(getAccessToken()).toBeNull();
  });

  it("single-flights concurrent callers into one network request", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(tokenResponse));

    const [a, b, c] = await Promise.all([
      restoreSession(),
      restoreSession(),
      restoreSession(),
    ]);

    expect(a).toBe("fresh-token");
    expect(b).toBe("fresh-token");
    expect(c).toBe("fresh-token");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("allows a fresh refresh after the previous one settled", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(tokenResponse));

    await restoreSession();
    await restoreSession();

    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});

describe("onAuthLost / notifyAuthLost", () => {
  beforeEach(() => {
    __resetSessionRestoreForTests();
    useAuthStore.getState().setSession("jwt", {
      id: "u1",
      email: "a@b.vn",
      roles: ["student"],
    });
  });
  afterEach(() => {
    __resetSessionRestoreForTests();
    useAuthStore.getState().clearSession();
  });

  it("clears the session and invokes registered handlers", () => {
    const handler = vi.fn();
    onAuthLost(handler);

    notifyAuthLost();

    expect(handler).toHaveBeenCalledTimes(1);
    expect(useAuthStore.getState().status).toBe("anonymous");
    expect(getAccessToken()).toBeNull();
  });

  it("stops calling a handler after it unsubscribes", () => {
    const handler = vi.fn();
    const unsubscribe = onAuthLost(handler);
    unsubscribe();

    notifyAuthLost();

    expect(handler).not.toHaveBeenCalled();
  });
});
