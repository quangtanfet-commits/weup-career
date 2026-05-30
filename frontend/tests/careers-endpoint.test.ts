import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { getCareer, listCareers } from "@/lib/api/endpoints/careers";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("careers endpoints", () => {
  beforeEach(() => {
    process.env.BACKEND_INTERNAL_URL = "http://backend:8000";
  });
  afterEach(() => {
    vi.restoreAllMocks();
    delete process.env.BACKEND_INTERNAL_URL;
  });

  it("listCareers forwards filters to GET /careers", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse([]));

    await listCareers({ riasec: "R", training_level: "university" });

    const [url] = fetchMock.mock.calls[0]!;
    expect(url).toContain("/api/v1/careers?");
    expect(url).toContain("riasec=R");
    expect(url).toContain("training_level=university");
  });

  it("getCareer requests the detail path and URL-encodes the id", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        id: "a/b",
        name: "x",
        field: "f",
        riasec_codes: [],
        training_level: "university",
        dieu5_code: "5a",
        version: 1,
        required_competencies: [],
        training_paths: "",
        labor_market_outlook: "",
        source_ref: "",
        pathways: [],
      }),
    );

    const career = await getCareer("a/b");

    expect(career.id).toBe("a/b");
    expect(fetchMock.mock.calls[0]![0]).toBe(
      "http://backend:8000/api/v1/careers/a%2Fb",
    );
  });
});
