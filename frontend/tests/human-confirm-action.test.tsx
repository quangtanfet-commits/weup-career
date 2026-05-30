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

// Mock the endpoint layer so the confirm hook resolves without a network.
const confirmRecommendation = vi.fn();
vi.mock("@/lib/api/endpoints/recommendations", async (importOriginal) => {
  const actual =
    await importOriginal<
      typeof import("@/lib/api/endpoints/recommendations")
    >();
  return {
    ...actual,
    confirmRecommendation: (...args: unknown[]) =>
      confirmRecommendation(...args),
  };
});

import { HumanConfirmAction } from "@/features/recommendations/HumanConfirmAction";

function renderAction(ui: ReactElement): RenderResult {
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

describe("HumanConfirmAction (CP-5 human-in-the-loop)", () => {
  beforeEach(() => {
    confirmRecommendation.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("CP-5: does NOT call confirm on mount — only after an explicit click", () => {
    renderAction(<HumanConfirmAction recoId="r1" />);

    // Rendering offers the choices but enacts nothing (no auto-apply).
    expect(
      screen.getByRole("button", {
        name: messages.recommendations.decision.accepted,
      }),
    ).toBeInTheDocument();
    expect(confirmRecommendation).not.toHaveBeenCalled();
  });

  it("CP-5: clicking a decision posts exactly that decision and fires onConfirmed", async () => {
    confirmRecommendation.mockResolvedValue({
      id: "r1",
      confirmed_by: "u1",
      confirmed_decision: "rejected",
    });
    const onConfirmed = vi.fn();
    const user = userEvent.setup();
    renderAction(<HumanConfirmAction recoId="r1" onConfirmed={onConfirmed} />);

    await user.click(
      screen.getByRole("button", {
        name: messages.recommendations.decision.rejected,
      }),
    );

    await waitFor(() => expect(confirmRecommendation).toHaveBeenCalledTimes(1));
    expect(confirmRecommendation).toHaveBeenCalledWith("r1", {
      decision: "rejected",
    });
    await waitFor(() => expect(onConfirmed).toHaveBeenCalledTimes(1));
  });

  it("surfaces a backend error message when confirm fails", async () => {
    const { ApiError } = await import("@/lib/api/errors");
    confirmRecommendation.mockRejectedValue(
      new ApiError(403, "Bạn không có quyền xác nhận gợi ý này", "FORBIDDEN"),
    );
    const user = userEvent.setup();
    renderAction(<HumanConfirmAction recoId="r1" />);

    await user.click(
      screen.getByRole("button", {
        name: messages.recommendations.decision.accepted,
      }),
    );

    expect(
      await screen.findByText("Bạn không có quyền xác nhận gợi ý này"),
    ).toBeInTheDocument();
  });
});
