import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";

import vi_messages from "@/messages/vi.json";

vi.mock("next-intl/server", () => ({
  getTranslations: async (ns: keyof typeof vi_messages) => {
    const table = vi_messages[ns] as Record<string, string>;
    return (key: string) => table[key] ?? `${String(ns)}.${key}`;
  },
}));

class NotFoundError extends Error {}
vi.mock("next/navigation", () => ({
  notFound: () => {
    throw new NotFoundError("NEXT_NOT_FOUND");
  },
}));

import ContentLibraryPage from "@/app/(public)/content/page";
import ContentDetailPage, {
  generateMetadata,
} from "@/app/(public)/content/[contentId]/page";
import type { ContentItem } from "@/lib/api/endpoints/content";

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
    body: "Đoạn một.\nĐoạn hai.",
    competency_code: "NL1",
    dieu5_code: "5a",
    depth: null,
    dev_phase: null,
    school_level: "lower_secondary",
    source_ref: "CTGDPT 2018",
    status: "published",
    version: 1,
  },
];

describe("Public content pages (anonymous RSC)", () => {
  beforeEach(() => {
    process.env.BACKEND_INTERNAL_URL = "http://backend:8000";
  });
  afterEach(() => {
    vi.restoreAllMocks();
    delete process.env.BACKEND_INTERNAL_URL;
  });

  it("ContentLibraryPage lists published items fetched anonymously", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(sample));

    render(await ContentLibraryPage());

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://backend:8000/api/v1/content");
    expect(new Headers(init?.headers).has("authorization")).toBe(false);
    expect(screen.getByText("Hiểu về bản thân")).toBeInTheDocument();
  });

  it("ContentLibraryPage shows the empty state when nothing is published", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse([]));
    render(await ContentLibraryPage());
    expect(screen.getByText(vi_messages.content.empty)).toBeInTheDocument();
  });

  it("ContentLibraryPage shows an error alert when the read fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ code: "INTERNAL", message: "lỗi" }, 500),
    );
    render(await ContentLibraryPage());
    expect(screen.getByRole("alert")).toHaveTextContent(
      vi_messages.content.loadError,
    );
  });

  it("ContentDetailPage renders the resolved published item", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(sample));

    render(
      await ContentDetailPage({
        params: Promise.resolve({ contentId: "ct1" }),
      }),
    );

    expect(
      screen.getByRole("heading", { level: 1, name: "Hiểu về bản thân" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Đoạn một\./)).toBeInTheDocument();
  });

  it("ContentDetailPage renders notFound() for an unknown id", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(sample));

    await expect(
      ContentDetailPage({ params: Promise.resolve({ contentId: "missing" }) }),
    ).rejects.toBeInstanceOf(NotFoundError);
  });

  it("generateMetadata uses the item title, or a fallback for an unknown id", async () => {
    // A fresh Response per call — a body can only be read once.
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      jsonResponse(sample),
    );

    const meta = await generateMetadata({
      params: Promise.resolve({ contentId: "ct1" }),
    });
    expect(meta.title).toBe("Hiểu về bản thân");

    const missing = await generateMetadata({
      params: Promise.resolve({ contentId: "missing" }),
    });
    expect(missing.title).toBe("Không tìm thấy nội dung");
  });
});
