import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";

const token = vi.fn<() => string | null>();
vi.mock("next/navigation", () => ({
  useSearchParams: () => ({ get: () => token() }),
}));

const verifyEmail = vi.fn();
vi.mock("@/lib/api/endpoints/auth", () => ({
  verifyEmail: (...args: unknown[]) => verifyEmail(...args),
}));

import { VerifyEmailView } from "@/features/auth/VerifyEmailView";
import { VerifyEmailClient } from "@/features/auth/VerifyEmailClient";
import { renderWithIntl, viMessages } from "./helpers/intl";

describe("VerifyEmailView", () => {
  it("renders the busy status while verifying", () => {
    renderWithIntl(<VerifyEmailView state="verifying" />);
    const status = screen.getByRole("status");
    expect(status).toHaveTextContent(viMessages.auth.verifying);
    expect(status).toHaveAttribute("aria-busy", "true");
  });

  it("renders the success state with a login CTA", () => {
    renderWithIntl(<VerifyEmailView state="success" />);
    expect(
      screen.getByRole("heading", { name: viMessages.auth.verifySuccessTitle }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(viMessages.auth.verifySuccessBody),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: viMessages.auth.goLoginCta }),
    ).toHaveAttribute("href", "/login");
  });

  it("renders the generic invalid state (no enumeration) with a login CTA", () => {
    renderWithIntl(<VerifyEmailView state="invalid" />);
    expect(
      screen.getByRole("heading", { name: viMessages.auth.verifyInvalidTitle }),
    ).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(
      viMessages.auth.verifyInvalidBody,
    );
    expect(
      screen.getByRole("link", { name: viMessages.auth.goLoginCta }),
    ).toHaveAttribute("href", "/login");
  });
});

describe("VerifyEmailClient", () => {
  beforeEach(() => {
    token.mockReset();
    verifyEmail.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the invalid state immediately and never calls the API when the token is missing", () => {
    token.mockReturnValue(null);
    renderWithIntl(<VerifyEmailClient />);

    expect(
      screen.getByRole("heading", { name: viMessages.auth.verifyInvalidTitle }),
    ).toBeInTheDocument();
    expect(verifyEmail).not.toHaveBeenCalled();
  });

  it("posts the token once and shows success on 204", async () => {
    token.mockReturnValue("good-token");
    verifyEmail.mockResolvedValue(undefined);
    renderWithIntl(<VerifyEmailClient />);

    await waitFor(() => expect(verifyEmail).toHaveBeenCalledWith("good-token"));
    expect(
      await screen.findByRole("heading", {
        name: viMessages.auth.verifySuccessTitle,
      }),
    ).toBeInTheDocument();
  });

  it("falls back to the generic invalid state when the API rejects", async () => {
    token.mockReturnValue("stale-token");
    verifyEmail.mockRejectedValue(new Error("401"));
    renderWithIntl(<VerifyEmailClient />);

    expect(
      await screen.findByRole("heading", {
        name: viMessages.auth.verifyInvalidTitle,
      }),
    ).toBeInTheDocument();
  });
});
