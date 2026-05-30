import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  inviteGuardian,
  grantConsent,
  revokeConsent,
} from "@/lib/api/endpoints/guardians";
import { useAuthStore } from "@/lib/auth/store";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("guardians endpoints", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    useAuthStore.getState().clearSession();
  });
  afterEach(() => {
    vi.restoreAllMocks();
    useAuthStore.getState().clearSession();
  });

  it("inviteGuardian POSTs the invite body to /guardians/invite", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "g1" }));

    await inviteGuardian({
      guardian_email: "me@example.vn",
      relationship: "mother",
    });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/guardians/invite");
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).body).toContain("me@example.vn");
  });

  it("grantConsent POSTs to /guardians/consent", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "c1" }));

    await grantConsent({ guardian_link_id: "l1" });

    expect(fetchMock.mock.calls[0]![0]).toBe(
      "http://localhost:8000/api/v1/guardians/consent",
    );
    expect((fetchMock.mock.calls[0]![1] as RequestInit).method).toBe("POST");
  });

  it("revokeConsent POSTs to /guardians/consent/revoke", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "c1" }));

    await revokeConsent({ child_user_id: "u1" });

    expect(fetchMock.mock.calls[0]![0]).toBe(
      "http://localhost:8000/api/v1/guardians/consent/revoke",
    );
    expect((fetchMock.mock.calls[0]![1] as RequestInit).method).toBe("POST");
  });
});
