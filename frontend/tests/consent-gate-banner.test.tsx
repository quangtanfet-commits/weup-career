import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { act, screen } from "@testing-library/react";

import { ConsentGateBanner } from "@/features/consent/ConsentGateBanner";
import { useAuthStore } from "@/lib/auth/store";
import { renderWithIntl, viMessages } from "./helpers/intl";

describe("ConsentGateBanner", () => {
  beforeEach(() => {
    act(() => useAuthStore.getState().clearSession());
  });
  afterEach(() => {
    act(() => useAuthStore.getState().clearSession());
  });

  it("renders children unchanged when the user is not consent-gated", () => {
    act(() => {
      useAuthStore.getState().setSession("jwt", {
        id: "u1",
        email: "a@b.vn",
        roles: ["working"],
        age_band: "adult",
        account_status: "active",
      });
    });

    renderWithIntl(
      <ConsentGateBanner>
        <p>Nội dung tính năng</p>
      </ConsentGateBanner>,
    );

    expect(screen.getByText("Nội dung tính năng")).toBeInTheDocument();
    expect(screen.queryByText(viMessages.consent.gateTitle)).toBeNull();
  });

  it("renders the gate notice + CTA for a child <16 without active consent", () => {
    act(() => {
      useAuthStore.getState().setSession("jwt", {
        id: "u1",
        email: "child@b.vn",
        roles: ["student"],
        age_band: "under_16",
        account_status: "pending_guardian_consent",
      });
    });

    renderWithIntl(
      <ConsentGateBanner>
        <p>Nội dung tính năng</p>
      </ConsentGateBanner>,
    );

    expect(screen.queryByText("Nội dung tính năng")).toBeNull();
    expect(screen.getByText(viMessages.consent.gateTitle)).toBeInTheDocument();
    const cta = screen.getByRole("link", { name: viMessages.consent.gateCta });
    expect(cta).toHaveAttribute("href", "/consent");
  });
});
