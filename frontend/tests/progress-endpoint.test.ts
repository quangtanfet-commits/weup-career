import { describe, it, expect, vi, afterEach } from "vitest";

import {
  getMyProgress,
  listCompetencies,
  recordIndicator,
  setDevPhase,
} from "@/lib/api/endpoints/progress";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("progress endpoints (F4)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("listCompetencies GETs /competencies", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse([]));

    await listCompetencies();

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toContain("/api/v1/competencies");
    expect((init as RequestInit | undefined)?.method ?? "GET").toBe("GET");
  });

  it("getMyProgress GETs /me/progress", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse([]));

    await getMyProgress();

    expect(fetchMock.mock.calls[0]![0]).toContain("/api/v1/me/progress");
  });

  it("setDevPhase POSTs the area+phase to /me/progress/dev-phase", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        jsonResponse({ area: "A_personal", dev_phase: "planning" }),
      );

    await setDevPhase({ area: "A_personal", dev_phase: "planning" });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toContain("/api/v1/me/progress/dev-phase");
    const request = init as RequestInit;
    expect(request.method).toBe("POST");
    expect(JSON.parse(request.body as string)).toEqual({
      area: "A_personal",
      dev_phase: "planning",
    });
  });

  it("recordIndicator POSTs the indicator id to /me/progress/indicators", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        advanced: true,
        competency_id: "c1",
        depth_achieved: "A",
        depth_label_vi: "Thực hiện",
      }),
    );

    const out = await recordIndicator({ indicator_id: "i1" });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toContain("/api/v1/me/progress/indicators");
    const request = init as RequestInit;
    expect(request.method).toBe("POST");
    expect(JSON.parse(request.body as string)).toEqual({ indicator_id: "i1" });
    expect(out.advanced).toBe(true);
    expect(out.depth_achieved).toBe("A");
  });
});
