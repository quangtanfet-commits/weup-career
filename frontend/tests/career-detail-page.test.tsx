import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";

import vi_messages from "@/messages/vi.json";

vi.mock("next-intl/server", () => ({
  getTranslations: async (ns: keyof typeof vi_messages) => {
    const table = vi_messages[ns] as Record<string, string>;
    return (key: string) => table[key] ?? `${String(ns)}.${key}`;
  },
}));

// `notFound()` throws a sentinel so the test can assert the 404 branch without
// pulling in the Next.js runtime.
class NotFoundError extends Error {}
vi.mock("next/navigation", () => ({
  notFound: () => {
    throw new NotFoundError("NEXT_NOT_FOUND");
  },
}));

import CareerDetailPage, {
  generateMetadata,
} from "@/app/(public)/careers/[careerId]/page";
import type { CareerDetail } from "@/lib/api/endpoints/careers";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const detail: CareerDetail = {
  id: "c1",
  name: "Kỹ sư phần mềm",
  field: "Công nghệ thông tin",
  riasec_codes: ["R", "I"],
  training_level: "university",
  dieu5_code: "5a",
  version: 1,
  required_competencies: ["NL1", "NL5"],
  training_paths: "Đại học CNTT 4 năm.",
  labor_market_outlook: "Nhu cầu cao trong 10 năm tới.",
  source_ref: "CTGDPT 2018",
  pathways: [
    {
      id: "p1",
      name: "Đại học chính quy",
      description: "Học 4 năm tại trường đại học.",
      type: "academic",
    },
  ],
};

describe("CareerDetailPage (anonymous RSC)", () => {
  beforeEach(() => {
    process.env.BACKEND_INTERNAL_URL = "http://backend:8000";
  });
  afterEach(() => {
    vi.restoreAllMocks();
    delete process.env.BACKEND_INTERNAL_URL;
  });

  it("renders the published career detail fetched anonymously", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(detail));

    render(
      await CareerDetailPage({ params: Promise.resolve({ careerId: "c1" }) }),
    );

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://backend:8000/api/v1/careers/c1");
    expect(new Headers(init?.headers).has("authorization")).toBe(false);
    expect(
      screen.getByRole("heading", { level: 1, name: "Kỹ sư phần mềm" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Nhu cầu cao trong 10 năm tới."),
    ).toBeInTheDocument();
    expect(screen.getByText("Đại học chính quy")).toBeInTheDocument();
  });

  it("renders notFound() when the backend returns 404 (existence-hiding)", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ code: "NOT_FOUND", message: "Không tìm thấy" }, 404),
    );

    await expect(
      CareerDetailPage({ params: Promise.resolve({ careerId: "missing" }) }),
    ).rejects.toBeInstanceOf(NotFoundError);
  });

  it("generateMetadata uses the career name, or a fallback on 404", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(detail));
    const meta = await generateMetadata({
      params: Promise.resolve({ careerId: "c1" }),
    });
    expect(meta.title).toBe("Kỹ sư phần mềm");

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ code: "NOT_FOUND", message: "x" }, 404),
    );
    const missing = await generateMetadata({
      params: Promise.resolve({ careerId: "missing" }),
    });
    expect(missing.title).toBe("Không tìm thấy nghề");
  });
});
