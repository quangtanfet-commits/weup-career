import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";

import vi_messages from "@/messages/vi.json";

// Resolve real Vietnamese copy from the catalog (mirrors career-library-page test).
vi.mock("next-intl/server", () => ({
  getTranslations: async (ns: keyof typeof vi_messages) => {
    const table = vi_messages[ns] as Record<string, string>;
    return (key: string) => table[key] ?? `${String(ns)}.${key}`;
  },
}));

import CareerLibraryPage from "@/app/(public)/careers/page";
import type { CareerSummary } from "@/lib/api/endpoints/careers";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const sample: CareerSummary[] = [
  {
    id: "c1",
    name: "Kỹ sư phần mềm",
    field: "Công nghệ thông tin",
    riasec_codes: ["R", "I"],
    training_level: "university",
    dieu5_code: "5a",
    version: 1,
  },
];

function searchParams(
  params: Record<string, string | string[] | undefined>,
): Promise<Record<string, string | string[] | undefined>> {
  return Promise.resolve(params);
}

describe("CareerLibraryPage (anonymous RSC, filtered)", () => {
  beforeEach(() => {
    process.env.BACKEND_INTERNAL_URL = "http://backend:8000";
  });
  afterEach(() => {
    vi.restoreAllMocks();
    delete process.env.BACKEND_INTERNAL_URL;
  });

  it("parses valid filters and forwards them to the anonymous fetch", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(sample));

    render(
      await CareerLibraryPage({
        searchParams: searchParams({
          riasec: "R",
          training_level: "university",
          pathway_type: "academic",
        }),
      }),
    );

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toContain("riasec=R");
    expect(url).toContain("training_level=university");
    expect(url).toContain("pathway_type=academic");
    expect(new Headers(init?.headers).has("authorization")).toBe(false);
    expect(screen.getByText("Kỹ sư phần mềm")).toBeInTheDocument();
  });

  it("drops invalid enum filters so the API never sees a bad value", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(sample));

    render(
      await CareerLibraryPage({
        searchParams: searchParams({
          riasec: "Z",
          training_level: "doctorate",
        }),
      }),
    );

    const [url] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://backend:8000/api/v1/careers");
  });

  it("renders the empty state when nothing is published", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse([]));

    render(await CareerLibraryPage({ searchParams: searchParams({}) }));

    expect(screen.getByText(vi_messages.careers.empty)).toBeInTheDocument();
  });

  it("renders an error alert when the backend read fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ code: "INTERNAL", message: "lỗi" }, 500),
    );

    render(await CareerLibraryPage({ searchParams: searchParams({}) }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      vi_messages.careers.loadError,
    );
  });
});
