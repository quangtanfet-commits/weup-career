import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  listContent,
  getPublicContentItem,
  type ContentItem,
} from "@/lib/api/endpoints/content";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const sample: ContentItem[] = [
  {
    id: "ct1",
    title: "Hiểu về bản thân",
    body: "Nội dung 5(a).",
    competency_code: "NL1",
    dieu5_code: "5a",
    depth: null,
    dev_phase: null,
    school_level: "lower_secondary",
    source_ref: "CTGDPT 2018",
    status: "published",
    version: 1,
  },
  {
    id: "ct2",
    title: "Khám phá nghề nghiệp",
    body: "Nội dung 5(c).",
    competency_code: "NL5",
    dieu5_code: "5c",
    depth: null,
    dev_phase: null,
    school_level: null,
    source_ref: "CTGDPT 2018",
    status: "published",
    version: 1,
  },
];

describe("content endpoints (anonymous public reads)", () => {
  beforeEach(() => {
    process.env.BACKEND_INTERNAL_URL = "http://backend:8000";
  });
  afterEach(() => {
    vi.restoreAllMocks();
    delete process.env.BACKEND_INTERNAL_URL;
  });

  it("listContent fetches /content anonymously and never forwards status", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(sample));

    const items = await listContent({
      dieu5_code: "5a",
      competency_code: "NL1",
    });

    expect(items).toHaveLength(2);
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe(
      "http://backend:8000/api/v1/content?dieu5_code=5a&competency_code=NL1",
    );
    expect(String(url)).not.toContain("status=");
    expect(new Headers(init?.headers).has("authorization")).toBe(false);
  });

  it("getPublicContentItem resolves a published item by id from the list", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(sample));

    const item = await getPublicContentItem("ct2");

    expect(item?.title).toBe("Khám phá nghề nghiệp");
  });

  it("getPublicContentItem returns null when no published item matches", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(sample));

    const item = await getPublicContentItem("missing");

    expect(item).toBeNull();
  });
});
