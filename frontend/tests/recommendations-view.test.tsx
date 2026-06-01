import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  render,
  screen,
  waitFor,
  act,
  type RenderResult,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement, ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";

import messages from "@/messages/vi.json";
import { defaultLocale } from "@/lib/i18n/config";
import { useAuthStore } from "@/lib/auth/store";

// Capture router.push so the onSuccess routing branch can be asserted.
const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace: vi.fn(), prefetch: vi.fn() }),
}));

// Mock the endpoint layer so the generate mutation resolves without a network.
const generateRecommendation = vi.fn();
vi.mock("@/lib/api/endpoints/recommendations", async (importOriginal) => {
  const actual =
    await importOriginal<
      typeof import("@/lib/api/endpoints/recommendations")
    >();
  return {
    ...actual,
    generateRecommendation: (...args: unknown[]) =>
      generateRecommendation(...args),
  };
});

import { RecommendationsView } from "@/features/recommendations/RecommendationsView";

function renderView(ui: ReactElement): RenderResult {
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

describe("RecommendationsView (F5 generate entry, CP-5/CP-6)", () => {
  beforeEach(() => {
    generateRecommendation.mockReset();
    push.mockReset();
    // Not consent-gated → the generate cluster renders (CP-1 gate stays open).
    act(() => useAuthStore.getState().clearSession());
  });
  afterEach(() => {
    act(() => useAuthStore.getState().clearSession());
    vi.restoreAllMocks();
  });

  it("renders the human-in-the-loop entry and does NOT auto-generate on mount", () => {
    renderView(<RecommendationsView />);

    expect(
      screen.getByRole("heading", { name: messages.recommendations.listTitle }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(messages.recommendations.humanInLoopNotice),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: messages.recommendations.generate }),
    ).toBeInTheDocument();
    // No auto-apply: nothing is generated until an explicit click.
    expect(generateRecommendation).not.toHaveBeenCalled();
    expect(push).not.toHaveBeenCalled();
  });

  it("on a successful generate, routes to the new recommendation's detail page", async () => {
    generateRecommendation.mockResolvedValue({
      id: "r1",
      payload: {},
      rationale: "x",
      requires_human_confirmation: true,
      confirmed_by: null,
      confirmed_decision: null,
      created_at: "2026-05-31T00:00:00Z",
    });
    const user = userEvent.setup();
    renderView(<RecommendationsView />);

    await user.click(
      screen.getByRole("button", { name: messages.recommendations.generate }),
    );

    await waitFor(() =>
      expect(generateRecommendation).toHaveBeenCalledTimes(1),
    );
    await waitFor(() =>
      expect(push).toHaveBeenCalledWith("/recommendations/r1"),
    );
  });

  it("surfaces the backend message when generate fails with an ApiError", async () => {
    const { ApiError } = await import("@/lib/api/errors");
    generateRecommendation.mockRejectedValue(
      new ApiError(403, "Bạn cần được giám hộ đồng ý trước", "FORBIDDEN"),
    );
    const user = userEvent.setup();
    renderView(<RecommendationsView />);

    await user.click(
      screen.getByRole("button", { name: messages.recommendations.generate }),
    );

    expect(
      await screen.findByText("Bạn cần được giám hộ đồng ý trước"),
    ).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });

  it("falls back to the generic error for a non-ApiError failure", async () => {
    generateRecommendation.mockRejectedValue(new Error("boom"));
    const user = userEvent.setup();
    renderView(<RecommendationsView />);

    await user.click(
      screen.getByRole("button", { name: messages.recommendations.generate }),
    );

    expect(
      await screen.findByText(messages.recommendations.genericError),
    ).toBeInTheDocument();
  });

  it("shows the pending label and disables the button while generating", async () => {
    let resolve: ((v: unknown) => void) | undefined;
    generateRecommendation.mockReturnValue(
      new Promise((r) => {
        resolve = r;
      }),
    );
    const user = userEvent.setup();
    renderView(<RecommendationsView />);

    await user.click(
      screen.getByRole("button", { name: messages.recommendations.generate }),
    );

    const pending = await screen.findByRole("button", {
      name: messages.recommendations.generating,
    });
    expect(pending).toBeDisabled();

    // Resolve to settle the mutation and avoid an act() warning on teardown.
    await act(async () => {
      resolve?.({
        id: "r9",
        payload: {},
        rationale: "x",
        requires_human_confirmation: true,
        confirmed_by: null,
        confirmed_decision: null,
        created_at: "2026-05-31T00:00:00Z",
      });
    });
  });
});
