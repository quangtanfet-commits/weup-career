import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { publicFetch } from "@/lib/api/server";
import { ApiError } from "@/lib/api/errors";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("publicFetch (anonymous RSC reads)", () => {
  beforeEach(() => {
    process.env.BACKEND_INTERNAL_URL = "http://backend:8000";
  });
  afterEach(() => {
    vi.restoreAllMocks();
    delete process.env.BACKEND_INTERNAL_URL;
  });

  it("calls the internal backend base + /api/v1 with NO Authorization header", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse([{ id: "c1" }]));

    const result = await publicFetch<{ id: string }[]>("/careers");

    expect(result).toEqual([{ id: "c1" }]);
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://backend:8000/api/v1/careers");
    const headers = new Headers(init?.headers);
    expect(headers.has("authorization")).toBe(false);
  });

  it("serialises defined query params and drops empty ones", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse([]));

    await publicFetch("/careers", {
      query: { riasec: "R", field: "", training_level: undefined },
    });

    const [url] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://backend:8000/api/v1/careers?riasec=R");
  });

  it("requests ISR revalidation (default 3600s)", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse([]));

    await publicFetch("/careers");

    const init = fetchMock.mock.calls[0]![1] as RequestInit & {
      next?: { revalidate?: number };
    };
    expect(init.next?.revalidate).toBe(3600);
  });

  it("throws ApiError carrying the backend error envelope on non-2xx", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ code: "NOT_FOUND", message: "Không tìm thấy" }, 404),
    );

    await expect(publicFetch("/careers/x")).rejects.toMatchObject({
      status: 404,
      code: "NOT_FOUND",
      message: "Không tìm thấy",
    });
    await expect(publicFetch("/careers/x")).rejects.toBeInstanceOf(ApiError);
  });
});
