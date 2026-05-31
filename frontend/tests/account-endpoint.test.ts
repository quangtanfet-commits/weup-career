import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  changePassword,
  deleteAccount,
  deleteChildAccount,
  exportChildData,
  exportData,
  getProfile,
  updateProfile,
} from "@/lib/api/endpoints/account";
import { useAuthStore, type SessionUser } from "@/lib/auth/store";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function noContent(): Response {
  return new Response(null, { status: 204 });
}

const meUser: SessionUser = {
  id: "u1",
  email: "me@example.vn",
  roles: ["student", "guardian"],
};

describe("account endpoints (Bearer, R:self/guardian)", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    useAuthStore.getState().setSession("me-token", meUser);
  });
  afterEach(() => {
    vi.restoreAllMocks();
    useAuthStore.getState().clearSession();
  });

  it("getProfile GETs /me/profile with the bearer token", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "u1" }));

    await getProfile();

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/me/profile");
    expect(new Headers(init?.headers).get("authorization")).toBe(
      "Bearer me-token",
    );
  });

  it("updateProfile PATCHes /me with the ProfileUpdateRequest body", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "u1" }));

    await updateProfile({
      school_level: "upper_secondary",
      user_type: "student",
    });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/me");
    expect((init as RequestInit).method).toBe("PATCH");
    expect((init as RequestInit).body).toContain("upper_secondary");
  });

  it("changePassword POSTs /me/password and tolerates 204", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(noContent());

    await changePassword({
      current_password: "old-secret",
      new_password: "new-secret-123",
    });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/me/password");
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).body).toContain("new-secret-123");
  });

  it("deleteAccount DELETEs /me", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ recovery_window_days: 30 }));

    await deleteAccount();

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/me");
    expect((init as RequestInit).method).toBe("DELETE");
  });

  it("exportData GETs /me/export", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ subject_id: "u1" }));

    await exportData();

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/me/export");
    expect(new Headers(init?.headers).get("authorization")).toBe(
      "Bearer me-token",
    );
  });

  it("exportChildData GETs /me/children/{id}/export (encoded id)", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ subject_id: "child a" }));

    await exportChildData("child a");

    const [url] = fetchMock.mock.calls[0]!;
    expect(url).toBe(
      "http://localhost:8000/api/v1/me/children/child%20a/export",
    );
  });

  it("deleteChildAccount DELETEs /me/children/{id} (encoded id)", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ recovery_window_days: 30 }));

    await deleteChildAccount("c1");

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/me/children/c1");
    expect((init as RequestInit).method).toBe("DELETE");
  });
});
