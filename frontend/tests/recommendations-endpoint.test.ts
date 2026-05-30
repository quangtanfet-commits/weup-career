import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  confirmRecommendation,
  generateRecommendation,
  getRecommendation,
} from "@/lib/api/endpoints/recommendations";
import { useAuthStore } from "@/lib/auth/store";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("recommendations endpoints (F5)", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    useAuthStore.getState().clearSession();
  });
  afterEach(() => {
    vi.restoreAllMocks();
    useAuthStore.getState().clearSession();
  });

  it("generateRecommendation POSTs to /recommendations with no body", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "r1", rationale: "vì sao" }, 201));

    await generateRecommendation();

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/recommendations");
    const request = init as RequestInit;
    expect(request.method).toBe("POST");
    // POST /recommendations takes no request body (create_recommendation).
    expect(request.body).toBeUndefined();
  });

  it("getRecommendation GETs /recommendations/{id}", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "r1", rationale: "vì sao" }));

    await getRecommendation("r1");

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/recommendations/r1");
    expect((init as RequestInit).method).toBeUndefined();
  });

  it("confirmRecommendation POSTs the decision to /recommendations/{id}/confirm", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        jsonResponse({ id: "r1", confirmed_decision: "accepted" }),
      );

    await confirmRecommendation("r1", { decision: "accepted" });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/recommendations/r1/confirm");
    const request = init as RequestInit;
    expect(request.method).toBe("POST");
    expect(JSON.parse(request.body as string)).toEqual({
      decision: "accepted",
    });
  });
});
