import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  listInstruments,
  submitAssessment,
  getResult,
  deleteResult,
} from "@/lib/api/endpoints/assessments";
import { useAuthStore } from "@/lib/auth/store";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("assessment endpoints (authed, sensitive)", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    useAuthStore.getState().setSession("tok", {
      id: "u1",
      email: "a@b.vn",
      roles: ["student"],
    });
  });
  afterEach(() => {
    vi.restoreAllMocks();
    useAuthStore.getState().clearSession();
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
  });

  it("listInstruments GETs /assessments", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse([]));

    await listInstruments();

    const [url] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/assessments");
  });

  it("submitAssessment POSTs answers to the typed submit path", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "r1" }));

    await submitAssessment("riasec", { answers: { R_1: 4 } });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/assessments/riasec/submit");
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).body).toBe(
      JSON.stringify({ answers: { R_1: 4 } }),
    );
    // The bearer token is attached — results are sensitive, never anonymous.
    expect(
      new Headers((init as RequestInit).headers).get("authorization"),
    ).toBe("Bearer tok");
  });

  it("getResult reads the audited per-result path and URL-encodes the id", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "a/b" }));

    await getResult("a/b");

    expect(fetchMock.mock.calls[0]![0]).toBe(
      "http://localhost:8000/api/v1/me/assessments/a%2Fb",
    );
  });

  it("deleteResult DELETEs the per-result path and resolves void on 204", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(null, { status: 204 }));

    await expect(deleteResult("r1")).resolves.toBeUndefined();

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/me/assessments/r1");
    expect((init as RequestInit).method).toBe("DELETE");
  });
});
