import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  render,
  screen,
  waitFor,
  type RenderResult,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement, ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";

import messages from "@/messages/vi.json";
import { defaultLocale } from "@/lib/i18n/config";
import type { RecommendationOut } from "@/lib/api/endpoints/recommendations";

// Mock the endpoint layer so the read query resolves/rejects without a network.
const getRecommendation = vi.fn();
vi.mock("@/lib/api/endpoints/recommendations", async (importOriginal) => {
  const actual =
    await importOriginal<
      typeof import("@/lib/api/endpoints/recommendations")
    >();
  return {
    ...actual,
    getRecommendation: (...args: unknown[]) => getRecommendation(...args),
  };
});

import { RecommendationDetailView } from "@/features/recommendations/RecommendationDetailView";

function makeReco(
  overrides: Partial<RecommendationOut> = {},
): RecommendationOut {
  return {
    id: "r1",
    payload: { suggestion: "Khám phá nhóm ngành Kỹ thuật" },
    rationale: "Kết quả RIASEC của bạn nghiêng về nhóm R và I.",
    requires_human_confirmation: true,
    confirmed_by: null,
    confirmed_decision: null,
    created_at: "2026-05-31T00:00:00Z",
    ...overrides,
  };
}

function renderDetail(ui: ReactElement): RenderResult {
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

describe("RecommendationDetailView (F5 read, CP-4/CP-5/CP-6)", () => {
  beforeEach(() => {
    getRecommendation.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows a loading status while the recommendation is being read", () => {
    // A never-resolving promise keeps the query in its loading state.
    getRecommendation.mockReturnValue(new Promise(() => {}));
    renderDetail(<RecommendationDetailView recoId="r1" />);

    expect(screen.getByRole("status")).toHaveTextContent(
      messages.recommendations.detailLoading,
    );
  });

  it("renders the recommendation card (rationale + payload) on success", async () => {
    getRecommendation.mockResolvedValue(makeReco());
    renderDetail(<RecommendationDetailView recoId="r1" />);

    expect(
      await screen.findByText(messages.recommendations.rationaleTitle),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Kết quả RIASEC của bạn nghiêng về nhóm R và I."),
    ).toBeInTheDocument();
  });

  it("CP-4: a 404 surfaces neutral not-found copy with NO retry (existence-hiding)", async () => {
    const { ApiError } = await import("@/lib/api/errors");
    getRecommendation.mockRejectedValue(
      new ApiError(404, "ignored", "NOT_FOUND"),
    );
    renderDetail(<RecommendationDetailView recoId="r1" />);

    expect(
      await screen.findByText(messages.recommendations.detailNotFound),
    ).toBeInTheDocument();
    // A not-found state must not offer a retry (it would leak existence probing).
    expect(
      screen.queryByRole("button", { name: messages.common.retry }),
    ).not.toBeInTheDocument();
  });

  it("a non-404 error shows the load-error copy and a retry that refetches", async () => {
    const { ApiError } = await import("@/lib/api/errors");
    getRecommendation.mockRejectedValue(
      new ApiError(500, "server", "SERVER_ERROR"),
    );
    const user = userEvent.setup();
    renderDetail(<RecommendationDetailView recoId="r1" />);

    expect(
      await screen.findByText(messages.recommendations.detailLoadError),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: messages.common.retry }),
    );
    await waitFor(() => expect(getRecommendation).toHaveBeenCalledTimes(2));
  });

  it("treats a resolved-but-undefined read as an error state, not a blank page", async () => {
    getRecommendation.mockResolvedValue(
      undefined as unknown as RecommendationOut,
    );
    renderDetail(<RecommendationDetailView recoId="r1" />);

    // Not an ApiError 404, so it falls through to the generic load-error copy.
    expect(
      await screen.findByText(messages.recommendations.detailLoadError),
    ).toBeInTheDocument();
  });
});
