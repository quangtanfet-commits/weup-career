import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { apiFetch } from "@/lib/api/client";
import { useAuthStore } from "@/lib/auth/store";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("apiFetch (authed client calls)", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    useAuthStore.getState().clearSession();
  });
  afterEach(() => {
    vi.restoreAllMocks();
    useAuthStore.getState().clearSession();
  });

  it("injects the in-memory bearer token and includes credentials", async () => {
    useAuthStore.getState().setSession("token-123", {
      id: "u1",
      email: "a@b.vn",
      roles: ["student"],
    });
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ ok: true }));

    await apiFetch("/auth/me");

    const init = fetchMock.mock.calls[0]![1] as RequestInit;
    const headers = new Headers(init.headers);
    expect(headers.get("authorization")).toBe("Bearer token-123");
    expect(init.credentials).toBe("include");
  });

  it("omits Authorization when there is no session", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ ok: true }));

    await apiFetch("/auth/me");

    const headers = new Headers(
      (fetchMock.mock.calls[0]![1] as RequestInit).headers,
    );
    expect(headers.has("authorization")).toBe(false);
  });

  it("serialises a JSON body and sets Content-Type", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "r1" }));

    await apiFetch("/recommendations", {
      method: "POST",
      body: { careerId: "c1" },
    });

    const init = fetchMock.mock.calls[0]![1] as RequestInit;
    expect(init.body).toBe(JSON.stringify({ careerId: "c1" }));
    expect(new Headers(init.headers).get("content-type")).toBe(
      "application/json",
    );
  });

  it("appends defined query params (dropping empty/undefined ones)", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse([]));

    await apiFetch("/recommendations", {
      query: { status: "pending", note: "", page: undefined },
    });

    const [url] = fetchMock.mock.calls[0]!;
    expect(url).toBe(
      "http://localhost:8000/api/v1/recommendations?status=pending",
    );
  });

  it("returns undefined for 204 No Content", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 204 }),
    );
    await expect(apiFetch("/auth/logout", { method: "POST" })).resolves.toBeUndefined();
  });

  it("throws ApiError on a non-2xx response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ code: "UNAUTHORIZED", message: "Hết phiên" }, 401),
    );
    await expect(apiFetch("/auth/me")).rejects.toMatchObject({
      status: 401,
      code: "UNAUTHORIZED",
    });
  });
});
