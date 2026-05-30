import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, type RenderResult } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";

import messages from "@/messages/vi.json";
import { defaultLocale } from "@/lib/i18n/config";
import { RecommendationCard } from "@/features/recommendations/RecommendationCard";
import type { RecommendationOut } from "@/lib/api/endpoints/recommendations";

function renderCard(ui: ReactElement): RenderResult {
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

describe("RecommendationCard (CP-5/CP-6)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("CP-6: always renders the rationale alongside the payload", () => {
    renderCard(<RecommendationCard recommendation={makeReco()} />);

    expect(
      screen.getByText(messages.recommendations.rationaleTitle),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Kết quả RIASEC của bạn nghiêng về nhóm R và I."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Khám phá nhóm ngành Kỹ thuật"),
    ).toBeInTheDocument();
  });

  it("CP-6: renders an error state (not a blank card) when rationale is missing", () => {
    renderCard(
      <RecommendationCard recommendation={makeReco({ rationale: "" })} />,
    );

    expect(
      screen.getByText(messages.recommendations.rationaleMissing),
    ).toBeInTheDocument();
    // The error card must NOT offer the confirm cluster for a broken reco.
    expect(
      screen.queryByText(messages.recommendations.decision.accepted),
    ).not.toBeInTheDocument();
  });

  it("CP-5: an unconfirmed reco shows 'chưa có hiệu lực' and the confirm cluster", () => {
    renderCard(<RecommendationCard recommendation={makeReco()} />);

    expect(
      screen.getByText(messages.recommendations.notEffective),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: messages.recommendations.decision.accepted,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: messages.recommendations.decision.rejected,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: messages.recommendations.decision.deferred,
      }),
    ).toBeInTheDocument();
    // FR-62: the "decision is yours" notice is always present.
    expect(
      screen.getByText(messages.recommendations.decisionIsYours),
    ).toBeInTheDocument();
  });

  it("CP-5: a confirmed reco shows the recorded decision and no confirm cluster", () => {
    renderCard(
      <RecommendationCard
        recommendation={makeReco({
          confirmed_by: "u1",
          confirmed_decision: "accepted",
        })}
      />,
    );

    expect(
      screen.queryByText(messages.recommendations.notEffective),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: messages.recommendations.decision.rejected,
      }),
    ).not.toBeInTheDocument();
    // The recorded human decision is surfaced.
    expect(screen.getByRole("status")).toHaveTextContent(/Chấp nhận/);
  });
});
