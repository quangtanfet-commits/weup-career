import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, type RenderResult } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";

import messages from "@/messages/vi.json";
import { defaultLocale } from "@/lib/i18n/config";

// Drive the page's `?school=` query param per test.
let searchValue: string | null = null;
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(searchValue ?? ""),
}));

vi.mock("@/lib/api/endpoints/counseling", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/lib/api/endpoints/counseling")>();
  return { ...actual, listSchoolStudents: vi.fn() };
});

import { listSchoolStudents } from "@/lib/api/endpoints/counseling";
import { ApiError } from "@/lib/api/errors";
import CounselorStudentsPage from "@/app/(app)/counselor/students/page";

const listStudentsMock = vi.mocked(listSchoolStudents);

function renderPage(ui: ReactElement): RenderResult {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <NextIntlClientProvider locale={defaultLocale} messages={messages}>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </NextIntlClientProvider>
    );
  }
  return render(ui, { wrapper: Wrapper });
}

describe("CounselorStudentsPage (FR-82, CP-3/CP-4)", () => {
  beforeEach(() => {
    listStudentsMock.mockReset();
    searchValue = null;
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("prompts for a school when no ?school= is present (no fetch)", () => {
    searchValue = null;
    renderPage(<CounselorStudentsPage />);

    expect(
      screen.getByText(messages.counselor.rosterNeedsSchool),
    ).toBeInTheDocument();
    expect(listStudentsMock).not.toHaveBeenCalled();
  });

  it("renders the de-sensitized roster for a school", async () => {
    searchValue = "school=sch-1";
    listStudentsMock.mockResolvedValue([
      { user_id: "u1", email: "hs1@example.vn", class_id: "10A1" },
    ]);

    renderPage(<CounselorStudentsPage />);

    expect(await screen.findByText("hs1@example.vn")).toBeInTheDocument();
    expect(listStudentsMock).toHaveBeenCalledWith("sch-1");
  });

  it("shows a NEUTRAL not-found state on 404 (no existence leak, CP-4)", async () => {
    searchValue = "school=sch-x";
    listStudentsMock.mockRejectedValue(
      new ApiError(404, "Not Found", "NOT_FOUND"),
    );

    renderPage(<CounselorStudentsPage />);

    expect(
      await screen.findByText(messages.counselor.notFoundNeutral),
    ).toBeInTheDocument();
    // Never surfaces a roster or a distinct "permission denied" message.
    expect(screen.queryByText("hs1@example.vn")).toBeNull();
  });
});
