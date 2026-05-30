import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  createSupportRequest,
  listSupportRequests,
} from "@/lib/api/endpoints/wellbeing";
import { useAuthStore } from "@/lib/auth/store";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("wellbeing endpoints", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    useAuthStore.getState().clearSession();
  });
  afterEach(() => {
    vi.restoreAllMocks();
    useAuthStore.getState().clearSession();
  });

  it("createSupportRequest POSTs the message to /wellbeing/support-request", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "sr1" }, 201));

    await createSupportRequest({ message: "Em muốn được hỗ trợ." });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/wellbeing/support-request");
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).body).toContain("Em muốn được hỗ trợ.");
  });

  it("listSupportRequests GETs /wellbeing/support-requests", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse([]));

    await listSupportRequests();

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/wellbeing/support-requests");
    // GET has no explicit method override in apiFetch options.
    expect((init as RequestInit).method).toBeUndefined();
  });
});
