import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";

import vi_messages from "@/messages/vi.json";

// The page renders Vietnamese UI-chrome via next-intl's server `getTranslations`.
// Resolve real strings from the catalog so the test asserts user-visible copy.
vi.mock("next-intl/server", () => ({
  getTranslations: async (ns: keyof typeof vi_messages) => {
    const table = vi_messages[ns] as Record<string, string>;
    return (key: string) => table[key] ?? `${String(ns)}.${key}`;
  },
}));

import CareerLibraryPage from "@/app/(public)/nghe-nghiep/page";
import { CareerSummary } from "@/lib/api/endpoints/careers";

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
  {
    id: "c2",
    name: "Điều dưỡng viên",
    field: "Y tế",
    riasec_codes: ["S"],
    training_level: "college",
    dieu5_code: "5a",
    version: 1,
  },
];

describe("CareerLibraryPage (anonymous RSC)", () => {
  beforeEach(() => {
    process.env.BACKEND_INTERNAL_URL = "http://backend:8000";
  });
  afterEach(() => {
    vi.restoreAllMocks();
    delete process.env.BACKEND_INTERNAL_URL;
  });

  it("fetches GET /api/v1/careers anonymously and renders the titles", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(sample));

    // RSC: the page is an async server component; await its element tree.
    render(await CareerLibraryPage());

    // The anonymous-RSC contract: correct URL, no Authorization header.
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://backend:8000/api/v1/careers");
    expect(new Headers(init?.headers).has("authorization")).toBe(false);

    expect(
      screen.getByRole("heading", { level: 1, name: "Thư viện nghề nghiệp" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Kỹ sư phần mềm")).toBeInTheDocument();
    expect(screen.getByText("Điều dưỡng viên")).toBeInTheDocument();
  });

  it("shows the empty state when the library has no published careers", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse([]));

    render(await CareerLibraryPage());

    expect(
      screen.getByText(vi_messages.careers.empty),
    ).toBeInTheDocument();
  });

  it("renders an error alert when the backend read fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ code: "INTERNAL", message: "lỗi" }, 500),
    );

    render(await CareerLibraryPage());

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(vi_messages.careers.loadError);
  });
});
