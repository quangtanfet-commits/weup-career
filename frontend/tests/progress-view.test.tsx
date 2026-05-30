import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act, render, screen, type RenderResult } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";

import messages from "@/messages/vi.json";
import { defaultLocale } from "@/lib/i18n/config";
import { useAuthStore } from "@/lib/auth/store";
import type { Competency, ProgressItem } from "@/lib/api/endpoints/progress";

// Mock the endpoint layer so the view's hooks resolve without a network.
vi.mock("@/lib/api/endpoints/progress", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/lib/api/endpoints/progress")>();
  return {
    ...actual,
    listCompetencies: vi.fn(),
    getMyProgress: vi.fn(),
  };
});

import { listCompetencies, getMyProgress } from "@/lib/api/endpoints/progress";
import { ProgressView } from "@/features/progress/ProgressView";

const listCompetenciesMock = vi.mocked(listCompetencies);
const getMyProgressMock = vi.mocked(getMyProgress);

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

function setAdultSession() {
  act(() => {
    useAuthStore.getState().setSession("jwt", {
      id: "u1",
      email: "a@b.vn",
      roles: ["student"],
      age_band: "adult",
      account_status: "active",
    });
  });
}

const competency: Competency = {
  area: "A_personal",
  code: "NL1",
  dieu5_codes: ["5a"],
  id: "c1",
  indicators: [],
  name_en: "Self-awareness",
  name_vi: "Tự nhận thức",
};

const progressItem: ProgressItem = {
  area: "A_personal",
  code: "NL1",
  competency_id: "c1",
  depth_achieved: "A",
  depth_label_vi: "Thực hiện",
  dev_phase: "exploration",
  name_vi: "Tự nhận thức",
};

describe("ProgressView (F4 page body)", () => {
  beforeEach(() => {
    act(() => useAuthStore.getState().clearSession());
  });
  afterEach(() => {
    vi.clearAllMocks();
    act(() => useAuthStore.getState().clearSession());
  });

  it("renders the K-A-R sections once data loads", async () => {
    setAdultSession();
    listCompetenciesMock.mockResolvedValue([competency]);
    getMyProgressMock.mockResolvedValue([progressItem]);

    renderView(<ProgressView />);

    expect(
      await screen.findByRole("heading", {
        level: 3,
        name: messages.progress.overviewHeading,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        level: 3,
        name: messages.progress.treeHeading,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        level: 3,
        name: messages.progress.devPhaseHeading,
      }),
    ).toBeInTheDocument();
  });

  it("shows an error + retry when a read fails", async () => {
    setAdultSession();
    listCompetenciesMock.mockRejectedValue(new Error("boom"));
    getMyProgressMock.mockResolvedValue([]);

    renderView(<ProgressView />);

    expect(
      await screen.findByText(messages.progress.loadError),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: messages.common.retry }),
    ).toBeInTheDocument();
  });

  it("consent-gates a child <16 without active consent (no authed fetch surfaced)", () => {
    act(() => {
      useAuthStore.getState().setSession("jwt", {
        id: "child",
        email: "c@b.vn",
        roles: ["student"],
        age_band: "under_16",
        account_status: "pending_guardian_consent",
      });
    });
    listCompetenciesMock.mockResolvedValue([competency]);
    getMyProgressMock.mockResolvedValue([progressItem]);

    renderView(<ProgressView />);

    // The gate replaces the feature body with the consent CTA.
    expect(screen.getByText(messages.consent.gateTitle)).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", {
        level: 3,
        name: messages.progress.overviewHeading,
      }),
    ).toBeNull();
  });
});
