import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  register,
  login,
  refresh,
  getMe,
  logout,
} from "@/lib/api/endpoints/auth";
import { useAuthStore } from "@/lib/auth/store";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const tokenResponse = {
  access_token: "t",
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

describe("auth endpoints", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    useAuthStore.getState().clearSession();
  });
  afterEach(() => {
    vi.restoreAllMocks();
    useAuthStore.getState().clearSession();
  });

  it("register POSTs the body to /auth/register", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(tokenResponse.user));

    await register({
      email: "a@b.vn",
      password: "Abcdef12",
      date_of_birth: "1995-01-01",
      school_level: "tertiary",
      user_type: "working",
    });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/auth/register");
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).body).toContain("a@b.vn");
  });

  it("login POSTs to /auth/login", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(tokenResponse));

    await login({ email: "a@b.vn", password: "pw" });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/auth/login");
    expect((init as RequestInit).method).toBe("POST");
  });

  it("refresh POSTs to /auth/refresh and skips the 401 interceptor", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(tokenResponse));

    await refresh();

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/auth/refresh");
    expect((init as RequestInit).method).toBe("POST");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("getMe GETs /auth/me", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(tokenResponse.user));

    await getMe();

    expect(fetchMock.mock.calls[0]![0]).toBe(
      "http://localhost:8000/api/v1/auth/me",
    );
  });

  it("logout POSTs /auth/logout and tolerates a 204", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(null, { status: 204 }));

    await expect(logout()).resolves.toBeUndefined();
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/auth/logout");
    expect((init as RequestInit).method).toBe("POST");
  });
});
